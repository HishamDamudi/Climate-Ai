import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import APP_NAME, API_VERSION, ALLOWED_ORIGINS, LOG_LEVEL
from routes import weather, districts, prediction, alerts, history, records, auth

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("climate_ai")


def _train_model_if_missing():
    """On a fresh deploy (e.g. Render) there's no cached model.pkl in the repo.
    Train it once on first boot so the API is usable without a custom build
    script. This takes a few seconds on the free tier."""
    model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ml", "model.pkl")
    if not os.path.exists(model_path):
        logger.info("model.pkl not found - training on startup...")
        from ml.train import main as train_main
        train_main()
        logger.info("Model training complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    _train_model_if_missing()
    yield


app = FastAPI(
    title=APP_NAME,
    version=API_VERSION,
    description=(
        "REST API for the Climate Intelligence & Heatwave Monitoring System. "
        "See /docs for interactive Swagger documentation."
    ),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router)
app.include_router(weather.router)
app.include_router(districts.router)
app.include_router(prediction.router)
app.include_router(alerts.router)
app.include_router(history.router)
app.include_router(records.router)


@app.get("/")
def root():
    return {"name": APP_NAME, "version": API_VERSION, "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "ok"}
