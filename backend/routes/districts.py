from fastapi import APIRouter, HTTPException
from services.data_service import data_service

router = APIRouter(prefix="/districts", tags=["districts"])


@router.get("")
def list_districts():
    return data_service.districts.to_dict(orient="records")


@router.get("/{district}/history")
def district_history(district: str, days: int = 60):
    df = data_service.district_series(district, days=days)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"District '{district}' not found")
    out = df.copy()
    out["date"] = out["date"].astype(str)
    cols = ["date", "district", "max_temp", "humidity", "wind_kmph",
            "rainfall_mm", "heat_index", "aqi", "uv_index"]
    return out[cols].to_dict(orient="records")


@router.get("/regions/summary")
def region_summary():
    return data_service.region_summary().to_dict(orient="records")
