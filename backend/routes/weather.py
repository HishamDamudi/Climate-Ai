from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from services.data_service import data_service

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("")
def get_current_weather(district: Optional[str] = Query(None)):
    """Latest observation for every district, or a single district if given."""
    snap = data_service.latest_snapshot()
    if district:
        snap = snap[snap["district"].str.lower() == district.lower()]
        if snap.empty:
            raise HTTPException(status_code=404, detail=f"District '{district}' not found")
    cols = ["date", "district", "state", "region", "lat", "lon", "max_temp",
            "humidity", "wind_kmph", "rainfall_mm", "heat_index", "aqi", "uv_index"]
    out = snap[cols].copy()
    out["date"] = out["date"].astype(str)
    return out.to_dict(orient="records")


@router.get("/national-summary")
def national_summary():
    snap = data_service.latest_snapshot()
    return {
        "avg_max_temp": round(float(snap["max_temp"].mean()), 1),
        "avg_humidity": round(float(snap["humidity"].mean()), 1),
        "avg_aqi": round(float(snap["aqi"].mean()), 1),
        "max_temp_district": snap.loc[snap["max_temp"].idxmax(), "district"],
        "max_temp_value": round(float(snap["max_temp"].max()), 1),
        "districts_monitored": int(len(snap)),
    }
