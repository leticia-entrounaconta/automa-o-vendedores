import logging
import os
from pathlib import Path

from app.settings.environment import load_environment

load_environment()


def ensure_file(path_file: Path) -> str:
    """Ensure file exists and return its string path. If not found, log warning."""
    if not path_file.is_file():
        logging.warning(f"Arquivo nao encontrado: {path_file}")
    return str(path_file)


# ── Paths ────────────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parents[2]
APP_DIR = BASE_DIR / "app"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

DOWNLOAD_DIR = APP_DIR / "temp_files"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ── URLs — configure in .env ─────────────────────────────────────────────────

BASE_URL = os.getenv("URL")
BASE_URL_2TECH = os.getenv("URL_2TECH")

# ── Timeouts ─────────────────────────────────────────────────────────────────

PAGE_LOAD_TIMEOUT = 30
ELEMENT_WAIT_TIMEOUT = 20
EXPLICITLY_WAIT = 20

# ── Derived paths ────────────────────────────────────────────────────────────

LOG_FILE_PATH = str(LOGS_DIR / "app.log")
DOWNLOAD_PATH = str(DOWNLOAD_DIR)
