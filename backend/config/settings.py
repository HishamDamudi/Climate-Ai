import os

APP_NAME = "Climate Intelligence & Heatwave Monitoring System API"
API_VERSION = "1.0.0"

# Comma-separated list, e.g. "http://localhost:5173,https://myapp.com"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# MongoDB - stores admin-uploaded weather records (Phase III/IV persistence layer).
# Point this at a real cluster (e.g. MongoDB Atlas) in production via env var.
# If unreachable, mongo_service transparently falls back to an in-process mock
# so local dev/tests never require a running MongoDB instance.
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "climate_ai")

