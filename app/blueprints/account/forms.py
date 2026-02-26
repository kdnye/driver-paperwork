from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import Length, Optional, URL


class ProfileForm(FlaskForm):
    full_name = StringField("Full name", validators=[Optional(), Length(max=120)])
    avatar_url = StringField("Avatar URL", validators=[Optional(), URL(), Length(max=512)])
    phone = StringField("Phone", validators=[Optional(), Length(max=50)])
    bio = TextAreaField("Bio", validators=[Optional(), Length(max=2000)])
    submit = SubmitField("Save profile")


class SettingsForm(FlaskForm):
    theme = SelectField(
        "Theme",
        choices=[("default", "Default"), ("light", "Light"), ("dark", "Dark")],
    )
    email_notifications = BooleanField("Email notifications")
    submit = SubmitField("Save settings")
