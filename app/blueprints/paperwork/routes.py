import base64
import binascii
import io
from urllib.parse import urlparse

from flask import Blueprint, render_template, request, flash, redirect, url_for, g, jsonify, session
from app.blueprints.auth.guards import require_employee_approval
from app.services.couchdrop import CouchdropService
from werkzeug.datastructures import FileStorage

paperwork_bp = Blueprint("paperwork", __name__)


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
    pod_picture_url = _coerce_http_url(payload.get("pod_picture_url"))
    signature_url = _coerce_http_url(payload.get("captured_signature_url"))

    for generated_file in generated_files:
        if not isinstance(generated_file, dict):
            continue

        normalized_name = (generated_file.get("filename") or "").lower()
        file_role = (generated_file.get("type") or generated_file.get("role") or "").lower()
        file_url = _coerce_http_url(
            generated_file.get("url")
            or generated_file.get("file_url")
            or generated_file.get("download_url")
        )
        if not file_url:
            continue

        descriptor = f"{normalized_name} {file_role}"
        if not pod_picture_url and any(token in descriptor for token in ["picture", "photo", "image"]):
            pod_picture_url = file_url
        if not signature_url and "signature" in descriptor:
            signature_url = file_url

    return pod_picture_url, signature_url


def _record_pod_history(payload, generated_files):
    pod_picture_url, signature_url = _extract_pod_links(payload, generated_files)
    if not pod_picture_url and not signature_url:
        return

    pod_reference = (
        payload.get("pod_reference")
        or payload.get("pod_id")
        or payload.get("pod_number")
        or payload.get("delivery_id")
        or "Unknown POD"
    )

    existing = session.get("pod_history") or []
    existing.insert(
        0,
        {
            "pod_reference": str(pod_reference),
            "pod_picture_url": pod_picture_url,
            "captured_signature_url": signature_url,
        },
    )
    session["pod_history"] = existing[:20]
    session.modified = True

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
        for file in files:
            if CouchdropService.upload_driver_paperwork(g.current_user, file):
                success_count += 1
        
        # Return lightweight JSON for sequential client-side uploads
        if is_ajax:
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
    for upload in uploads:
        if CouchdropService.upload_driver_paperwork(g.current_user, upload):
            success_count += 1

    if success_count != len(uploads):
        return jsonify({"error": "One or more POD files failed to upload."}), 502

    _record_pod_history(payload, generated_files)

    return jsonify({"success_count": success_count}), 200
