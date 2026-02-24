import os
from dotenv import load_dotenv


load_dotenv()


def _str_to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _is_production() -> bool:
    return _str_to_bool(os.getenv("FSI_PRODUCTION"), default=False) or os.getenv("APP_ENV", "").lower() in {
        "prod",
        "production",
    }


def _get_env(name: str, default: str | None = None, required_in_production: bool = False) -> str:
    value = os.getenv(name, default)
    if required_in_production and _is_production() and not value:
        raise RuntimeError(
            f"Missing required environment variable '{name}'. "
            "In Cloud Run, wire this from Secret Manager using --set-secrets."
        )
    if value is None:
        raise RuntimeError(f"Environment variable '{name}' is not set.")
    return value


def get_runtime_config() -> dict:
    return {
        # Set by Secret Manager in production.
        "SECRET_KEY": _get_env("SECRET_KEY", "dev-only-change-me", required_in_production=True),
        # SQLAlchemy/psycopg connection string set via Secret Manager in production.
        "SQLALCHEMY_DATABASE_URI": _get_env(
            "DATABASE_URL",
            "postgresql+psycopg://localhost/fsi_app",
            required_in_production=True,
        ),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "DEBUG": _str_to_bool(os.getenv("DEBUG"), default=False),
        # Cloud Run injects this automatically; local dev defaults to 8080.
        "PORT": int(os.getenv("PORT", "8080")),
        # Optional hardening toggles.
        "SESSION_COOKIE_SECURE": _str_to_bool(os.getenv("SESSION_COOKIE_SECURE"), default=_is_production()),
        "REMEMBER_COOKIE_SECURE": _str_to_bool(os.getenv("REMEMBER_COOKIE_SECURE"), default=_is_production()),
    }
