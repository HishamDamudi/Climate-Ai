import os

APP_NAME = "Climate Intelligence & Heatwave Monitoring System API"
API_VERSION = "1.0.0"

# Comma-separated list, e.g. "http://localhost:5173,https://myapp.com"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
