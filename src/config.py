"""Database settings in one place: environment variables with local defaults."""
import os


def get_db_config() -> dict:
    return {
        "host": os.environ.get("DB_HOST", "localhost"),
        "user": os.environ.get("DB_USER", "phase4"),
        "password": os.environ.get("DB_PASS", "phase4"),
        "database": os.environ.get("DB_NAME", "eukonkanto_db"),
        "charset": "utf8mb4",
    }
