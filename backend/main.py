import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config.settings import APP_NAME, API_VERSION, ALLOWED_ORIGINS, LOG_LEVEL
from routes import weather, districts, prediction, alerts, history, records, auth

logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("climate_ai")

app = FastAPI(
    title=APP_NAME,
    version=API_VERSION,
    description=(
        "REST API for the Climate Intelligence & Heatwave Monitoring System. "
        "See /docs for interactive Swagger documentation."
    ),
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
