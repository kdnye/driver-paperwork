from flask import Blueprint, abort, render_template

from models import Role


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.get("/login")
def login_page():
    return render_template("auth/login.html")


@auth_bp.get("/gate/<role>")
def gate(role: str):
    allowed_roles = {item.value for item in Role}
    if role.upper() not in allowed_roles:
        abort(403)
    return {"role": role.upper(), "allowed": True}
