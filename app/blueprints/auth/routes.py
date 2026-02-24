from flask import Blueprint, abort, g, jsonify, redirect, render_template, request, session, url_for

from app import limiter
from app.blueprints.auth.guards import _load_current_user, require_employee_approval
from app.rate_limits import (
    AUTH_LOGIN_PAGE_LIMIT,
    AUTH_LOGIN_SUBMIT_BURST_LIMIT,
    AUTH_LOGIN_SUBMIT_LIMIT,
)
from app.services.rbac import evaluate_access
from models import User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.before_app_request
def attach_current_user():
    g.current_user = _load_current_user()


@auth_bp.get("/login")
@limiter.limit(AUTH_LOGIN_PAGE_LIMIT)
def login_page():
    return render_template("auth/login.html")


@auth_bp.post("/login")
# Route-level overrides intentionally tighten credential endpoints beyond
# app-level defaults to reduce brute-force and burst abuse risk.
@limiter.limit(AUTH_LOGIN_SUBMIT_LIMIT)
@limiter.limit(AUTH_LOGIN_SUBMIT_BURST_LIMIT)
def login_submit():
    email = request.form.get("email", "").strip().lower()
    user = User.query.filter_by(email=email).first()
    if user is None:
        abort(401)

    session["current_user_id"] = user.id
    return redirect(url_for("auth.post_login"))


@auth_bp.get("/pending-approval")
def pending_approval():
    return render_template("auth/pending_approval.html"), 403


@auth_bp.get("/post-login")
@require_employee_approval(redirect_endpoint="auth.pending_approval")
def post_login():
    return {"message": "Welcome to the employee portal."}


@auth_bp.get("/internal/dashboard")
@require_employee_approval(redirect_endpoint="auth.pending_approval")
def internal_dashboard():
    return {"dashboard": "internal-tools"}


@auth_bp.get("/gate/<resource>/<action>")
@require_employee_approval()
def gate(resource: str, action: str):
    user = g.current_user
    decision = evaluate_access(user_role=user.role, resource=resource, action=action)

    if not decision.allowed:
        return jsonify({"error": "Access denied.", "detail": decision.message}), 403

    return {"resource": resource.lower(), "action": action.lower(), "allowed": True}
