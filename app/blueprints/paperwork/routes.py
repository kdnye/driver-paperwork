from flask import Blueprint, render_template, request, flash, redirect, url_for, g
from app.blueprints.auth.guards import require_employee_approval
from app.services.couchdrop import CouchdropService

paperwork_bp = Blueprint("paperwork", __name__)

@paperwork_bp.route("/upload", methods=["GET", "POST"])
@require_employee_approval()
def upload():
    if request.method == "POST":
        files = request.files.getlist("scans")
        if not files or files[0].filename == '':
            flash("No files selected.")
            return redirect(request.url)
            
        if len(files) > 100:
            flash("Batch exceeds 100 file limit.")
            return redirect(request.url)

        success_count = 0
        for file in files:
            # Service creates structure: /Paperwork/{Driver Name}/{Date}/
            if CouchdropService.upload_driver_paperwork(g.current_user, file):
                success_count += 1
        
        flash(f"Successfully uploaded {success_count} documents.")
        return redirect(url_for("paperwork.history"))

    return render_template("paperwork/upload.html", title="Batch Upload")

@paperwork_bp.get("/history")
@require_employee_approval()
def history():
    return render_template("paperwork/history.html", title="Upload History")
