import os
from pathlib import Path

PROJECT_NAME = os.getenv("PROJECT_NAME", "perf-calc")

_default_db_path = Path(__file__).resolve().parents[2] / "perf_calc.db"
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{_default_db_path.as_posix()}",
)

SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"

DEFAULT_RULE_SET_CODE = os.getenv("DEFAULT_RULE_SET_CODE", "default")
