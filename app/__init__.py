from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

from app.config import get_runtime_config


db = SQLAlchemy()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])


def create_app(config_overrides: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.update(get_runtime_config())

    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    from app.blueprints.auth.routes import auth_bp

    app.register_blueprint(auth_bp)

    @app.get("/")
    def index():
        return "FSI boilerplate is ready."

    return app
