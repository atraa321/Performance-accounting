import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _resolve_runtime_path(raw_path: str) -> Path:
    path = Path(raw_path).expanduser()
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


RUNTIME_DIR = _resolve_runtime_path(os.getenv("PERF_RUNTIME_DIR", ".runtime"))
LOG_DIR = RUNTIME_DIR / "logs"
TMP_DIR = RUNTIME_DIR / "tmp"
DEFAULT_DB_PATH = _resolve_runtime_path(os.getenv("PERF_DB_PATH", str(RUNTIME_DIR / "perf_calc.db")))

for directory in (RUNTIME_DIR, LOG_DIR, TMP_DIR):
    directory.mkdir(parents=True, exist_ok=True)
