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
    # 1. Retrieve individual components from Cloud Run secrets
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS")
    db_name = os.getenv("DB_NAME")
    
    # 2. Use the established FSI Cloud SQL connection name
    cloud_sql_con = "quote-tool-483716:us-central1:quote-postgres"

    # 3. Construct the dynamic connection string
    # This removes the need for a manual DATABASE_URL environment variable
    database_url = f"postgresql+psycopg://{db_user}:{db_pass}@/{db_name}?host=/cloudsql/{cloud_sql_con}"

    return {
        # Ensure the secret key matches the Expenses app for shared sessions
        "SECRET_KEY": _get_env("SECRET_KEY", "dev-only-change-me", required_in_production=True),
        "SQLALCHEMY_DATABASE_URI": database_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "DEBUG": _str_to_bool(os.getenv("DEBUG"), default=False),
        "PORT": int(os.getenv("PORT", "8080")),
        "SESSION_COOKIE_SECURE": _str_to_bool(os.getenv("SESSION_COOKIE_SECURE"), default=_is_production()),
        "REMEMBER_COOKIE_SECURE": _str_to_bool(os.getenv("REMEMBER_COOKIE_SECURE"), default=_is_production()),
    }
    }
