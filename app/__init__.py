from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from app.config import get_runtime_config
from app.rate_limits import DEFAULT_DAILY_LIMIT, DEFAULT_HOURLY_LIMIT


db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(
    key_func=get_remote_address,
    # Per-route `@limiter.limit(...)` decorators may override these broad defaults
    # for sensitive/write-heavy endpoints (for example, auth credential routes).
    default_limits=[DEFAULT_DAILY_LIMIT, DEFAULT_HOURLY_LIMIT],
)


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(
        __name__,
        instance_relative_config=False,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.update(get_runtime_config())

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    from app.blueprints.auth.routes import auth_bp
    from app.blueprints.paperwork.routes import paperwork_bp 

    app.register_blueprint(auth_bp)
    app.register_blueprint(paperwork_bp) # Ensure this is registered

    # Update index to redirect to login instead of the boilerplate message
    @app.get("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("auth.login_page"))

    return app
