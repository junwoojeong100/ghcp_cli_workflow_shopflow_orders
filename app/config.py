"""Environment settings. Every value can be overridden with an environment variable."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def db_path() -> str:
    return os.environ.get("DB_PATH", str(BASE_DIR / "data" / "orders.db"))


def env_name() -> str:
    return os.environ.get("APP_ENV", "local")


def admin_token() -> str:
    return os.environ.get("ADMIN_TOKEN", "demo-admin-token")


def log_path() -> str | None:
    return os.environ.get("LOG_PATH")


def app_version() -> str:
    version_file = BASE_DIR / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"
