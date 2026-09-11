import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"
DATA_DIR = BACKEND_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DATA_DIR / "aegiscare.db"

SECRET_KEY = os.getenv("CAREAURA_SECRET_KEY", os.getenv("AEGISCARE_SECRET_KEY", "careaura-health-os-production-secret-2026-secure"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

APP_NAME = "CareAura Health OS"
APP_VERSION = "3.0.0"
API_PREFIX = "/api"
