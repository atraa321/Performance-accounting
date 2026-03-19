import os

from app.core.paths import DEFAULT_DB_PATH

PROJECT_NAME = os.getenv("PROJECT_NAME", "perf-calc")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DEFAULT_DB_PATH.as_posix()}",
)

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

DEFAULT_RULE_SET_CODE = os.getenv("DEFAULT_RULE_SET_CODE", "default")
