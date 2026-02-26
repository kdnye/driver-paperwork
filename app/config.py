import os
import urllib.parse # Add this import at the top
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
    # 1. Use _get_env to ensure the app crashes loudly on startup if secrets are missing.
    # 2. Use quote_plus to safely encode passwords containing special characters (like @ or /).
    db_user = urllib.parse.quote_plus(_get_env("DB_USER", required_in_production=True))
    db_pass = urllib.parse.quote_plus(_get_env("DB_PASS", required_in_production=True))
    db_name = _get_env("DB_NAME", required_in_production=True)
    
    # Established FSI Cloud SQL connection name
    cloud_sql_con = "quote-tool-483716:us-central1:quote-postgres"

    # Safely constructed dynamic connection string
    database_url = f"postgresql+psycopg://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{cloud_sql_con}"

    return {
        "SECRET_KEY": _get_env("SECRET_KEY", "dev-only-change-me", required_in_production=True),
        "SQLALCHEMY_DATABASE_URI": database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "DEBUG": _str_to_bool(os.getenv("DEBUG"), default=False),
        "PORT": int(os.getenv("PORT", "8080")),
        "SESSION_COOKIE_SECURE": _str_to_bool(os.getenv("SESSION_COOKIE_SECURE"), default=_is_production()),
        "REMEMBER_COOKIE_SECURE": _str_to_bool(os.getenv("REMEMBER_COOKIE_SECURE"), default=_is_production()),
    }
