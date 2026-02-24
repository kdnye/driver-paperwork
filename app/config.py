import os
from dotenv import load_dotenv


load_dotenv()


def _str_to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_runtime_config() -> dict:
    return {
        "SECRET_KEY": os.getenv("SECRET_KEY", "dev-only-change-me"),
        "SQLALCHEMY_DATABASE_URI": os.getenv("DATABASE_URL", "postgresql+psycopg://localhost/fsi_app"),
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "DEBUG": _str_to_bool(os.getenv("DEBUG"), default=False),
        "PORT": int(os.getenv("PORT", "8080")),
    }
