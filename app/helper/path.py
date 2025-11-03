import os
from app.core.config import settings
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))       # /app/core
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))  # /project-dir
LOGS_DIR = os.path.join(PROJECT_ROOT, "uploads", "logs")
LOGS_URL = f"{settings.base_url}/uploads/logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)