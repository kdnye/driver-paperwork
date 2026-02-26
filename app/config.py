import os
from dotenv import load_dotenv
from sqlalchemy import URL # Add this import at the top

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
    # 1. Fetch and safely strip trailing newlines (\n) from Secret Manager
    db_user = _get_env("DB_USER", required_in_production=True).strip()
    db_pass = _get_env("DB_PASS", required_in_production=True).strip()
    db_name = _get_env("DB_NAME", required_in_production=True).strip()
    
    cloud_sql_con = "quote-tool-483716:us-central1:quote-postgres"

    # 2. FIXED: Use 'query' to properly format the Unix Socket path for Cloud Run
    db_url = URL.create(
        drivername="postgresql+psycopg",
        username=db_user,
        password=db_pass,
        database=db_name,
        query={"host": f"/cloudsql/{cloud_sql_con}"}  # <--- This is the critical change
    )

    return {
        "SECRET_KEY": _get_env("SECRET_KEY", "dev-only-change-me", required_in_production=True).strip(),
        # Render the URL object to a string securely
        "SQLALCHEMY_DATABASE_URI": db_url.render_as_string(hide_password=False),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "DEBUG": _str_to_bool(os.getenv("DEBUG"), default=False),
        "PORT": int(os.getenv("PORT", "8080")),
        "SESSION_COOKIE_SECURE": _str_to_bool(os.getenv("SESSION_COOKIE_SECURE"), default=_is_production()),
        "REMEMBER_COOKIE_SECURE": _str_to_bool(os.getenv("REMEMBER_COOKIE_SECURE"), default=_is_production()),
    }
