import base64
import binascii
import io
from urllib.parse import urlparse

from flask import Blueprint, render_template, request, flash, redirect, url_for, g, jsonify, session
from app import db
from app.blueprints.auth.guards import require_employee_approval
from app.services.volume_storage import VolumeStorageService
from app.services.gcs import generate_signed_url
from models import PodSubmission
from werkzeug.datastructures import FileStorage

paperwork_bp = Blueprint("paperwork", __name__)


def _get_stream_size(file_storage):
    stream = getattr(file_storage, "stream", None)
    if stream is None or not hasattr(stream, "seek"):
        return None

    try:
        current = stream.tell()
        stream.seek(0, io.SEEK_END)
        size = stream.tell()
        stream.seek(current)
        return size
    except Exception:
        return None


def _build_generated_upload(encoded_file, default_filename="generated-upload.bin"):
    if not isinstance(encoded_file, dict):
        raise ValueError("Each generated file payload must be an object.")

    encoded_data = encoded_file.get("content_base64") or encoded_file.get("content")
    if not isinstance(encoded_data, str) or not encoded_data.strip():
        raise ValueError("Generated file content is required.")

    try:
        decoded_bytes = base64.b64decode(encoded_data, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("Generated file content contains invalid base64 data.") from exc

    if not decoded_bytes:
        raise ValueError("Generated file content decodes to empty bytes.")

    stream = io.BytesIO(decoded_bytes)
    stream.seek(0)

    filename = encoded_file.get("filename") or default_filename
    content_type = encoded_file.get("content_type") or "application/octet-stream"

    upload = FileStorage(stream=stream, filename=filename, content_type=content_type)
    upload.stream.seek(0)
    return upload


def _coerce_http_url(value):
    if not isinstance(value, str):
        return None

    candidate = value.strip()
    if not candidate:
        return None

    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"}:
        return None
    if not parsed.netloc:
        return None

    return candidate


def _extract_pod_links(payload, generated_files):
    pod_picture_url = _resolve_public_url(
        payload.get("pod_picture_url") or payload.get("photo_blob_name")
    )
    signature_url = _resolve_public_url(
        payload.get("captured_signature_url") or payload.get("signature_blob_name")
    )

    for generated_file in generated_files:
        if not isinstance(generated_file, dict):
            continue

        normalized_name = (generated_file.get("filename") or "").lower()
        file_role = (generated_file.get("type") or generated_file.get("role") or "").lower()
        file_url = _resolve_public_url(
            generated_file.get("url")
            or generated_file.get("file_url")
            or generated_file.get("download_url")
            or generated_file.get("blob_name")
            or generated_file.get("path")
            or generated_file.get("uri")
        )
        if not file_url:
            continue

        descriptor = f"{normalized_name} {file_role}"
        if not pod_picture_url and any(token in descriptor for token in ["picture", "photo", "image"]):
            pod_picture_url = file_url
        if not signature_url and "signature" in descriptor:
            signature_url = file_url

    return pod_picture_url, signature_url


def _resolve_public_url(value):
    url = _coerce_http_url(value)
    if url:
        return url

    if not isinstance(value, str):
        return None

    return generate_signed_url(value)


def _record_pod_history(payload, generated_files):
    pod_picture_url, signature_url = _extract_pod_links(payload, generated_files)
    if not pod_picture_url and not signature_url:
        return

    pod_reference = _resolve_pod_reference(payload)

    existing = session.get("pod_history") or []
    existing.insert(
        0,
        {
            "pod_reference": pod_reference,
            "pod_picture_url": pod_picture_url,
            "captured_signature_url": signature_url,
        },
    )
    session["pod_history"] = existing[:20]
    session.modified = True


def _resolve_pod_reference(payload):
    return str(
        payload.get("pod_reference")
        or payload.get("pod_id")
        or payload.get("pod_number")
        or payload.get("delivery_id")
        or "Unknown POD"
    )


def _persist_pod_submissions(payload, generated_files, uploaded_uris):
    pod_picture_url, signature_url = _extract_pod_links(payload, generated_files)
    pod_reference = _resolve_pod_reference(payload)

    records = []
    for uri in uploaded_uris:
        if not isinstance(uri, str) or not uri.strip():
            raise ValueError("POD upload did not return a valid file URI.")

        records.append(
            PodSubmission(
                user_id=g.current_user.id,
                pod_reference=pod_reference,
                uploaded_file_uri=uri.strip(),
                pod_picture_url=pod_picture_url,
                captured_signature_url=signature_url,
            )
        )

    if not records:
        raise ValueError("No POD files were persisted because no valid upload URIs were returned.")

    db.session.add_all(records)
    db.session.commit()

@paperwork_bp.route("/upload", methods=["GET", "POST"])
@require_employee_approval()
def upload():
    if request.method == "POST":
        files = request.files.getlist("scans")
        is_ajax = request.headers.get("Accept") == "application/json"
        
        if not files or files[0].filename == '':
            if is_ajax: return jsonify({"error": "No files selected."}), 400
            flash("No files selected.")
            return redirect(request.url)
            
        if len(files) > 100:
            if is_ajax: return jsonify({"error": "Batch exceeds 100 file limit."}), 400
            flash("Batch exceeds 100 file limit.")
            return redirect(request.url)

        success_count = 0
        failure_count = 0
        for file in files:
            if not file or not file.filename:
                failure_count += 1
                continue

            file_size = _get_stream_size(file)
            if file_size == 0:
                failure_count += 1
                continue

            if VolumeStorageService.upload_driver_paperwork(g.current_user, file):
                success_count += 1
            else:
                failure_count += 1

        # Return lightweight JSON for sequential client-side uploads
        if is_ajax:
            if failure_count > 0:
                return jsonify({"error": "Upload failed.", "success_count": success_count}), 422
            return jsonify({"success_count": success_count}), 200
        
        # Fallback for standard synchronous post
        flash(f"Successfully uploaded {success_count} documents.")
        return redirect(url_for("paperwork.history"))

    return render_template("paperwork/upload.html", title="Batch Upload")

@paperwork_bp.get("/history")
@require_employee_approval()
def history():
    return render_template(
        "paperwork/history.html",
        title="Upload History",
        pod_history=session.get("pod_history") or [],
    )


@paperwork_bp.post("/pod/submit")
@require_employee_approval()
def submit_pod():
    payload = request.get_json(silent=True) or {}
    generated_files = payload.get("generated_files") or []

    if not isinstance(generated_files, list) or not generated_files:
        return jsonify({"error": "generated_files is required."}), 400

    uploads = []
    try:
        for index, generated_file in enumerate(generated_files, start=1):
            upload = _build_generated_upload(
                generated_file,
                default_filename=f"pod-generated-{index}.bin",
            )
            uploads.append(upload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    # Defensive reset: ensure all streams are at position 0 before forwarding.
    for upload in uploads:
        upload.stream.seek(0)

    success_count = 0
    uploaded_uris = []
    try:
        for upload in uploads:
            uploaded_uri = VolumeStorageService.upload_driver_paperwork(g.current_user, upload)
            if not uploaded_uri:
                raise ValueError("One or more POD files failed to upload.")

            uploaded_uris.append(uploaded_uri)
            success_count += 1

        _persist_pod_submissions(payload, generated_files, uploaded_uris)
    except ValueError as exc:
        db.session.rollback()
        return jsonify({"error": f"POD submission rolled back: {exc}"}), 422
    except Exception:
        db.session.rollback()
        return jsonify({"error": "POD submission rolled back due to an internal persistence error."}), 500

    _record_pod_history(payload, generated_files)

    return jsonify({"success_count": success_count}), 200
