from flask import Blueprint, flash, g, redirect, render_template, url_for

from app import db
from app.blueprints.account.forms import ProfileForm, SettingsForm
from app.blueprints.auth.guards import require_authenticated


account_bp = Blueprint("account", __name__, url_prefix="/account")


@account_bp.route("/profile", methods=["GET", "POST"])
@require_authenticated()
def profile():
    user = g.current_user
    form = ProfileForm(obj=user)

    if form.validate_on_submit():
        user.full_name = form.full_name.data.strip() if form.full_name.data else None
        user.avatar_url = form.avatar_url.data.strip() if form.avatar_url.data else None
        user.phone = form.phone.data.strip() if form.phone.data else None
        user.bio = form.bio.data.strip() if form.bio.data else None
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("account.profile"))

    return render_template("account/profile.html", title="Profile", form=form)


@account_bp.route("/settings", methods=["GET", "POST"])
@require_authenticated()
def settings():
    user = g.current_user
    form = SettingsForm(obj=user)

    if form.validate_on_submit():
        user.theme = form.theme.data
        user.email_notifications = form.email_notifications.data
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("account.settings"))

    return render_template("account/settings.html", title="Settings", form=form)
