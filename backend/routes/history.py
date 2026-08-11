from fastapi import APIRouter, Query
from services.data_service import data_service

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
def national_trend(days: int = Query(90, ge=7, le=365)):
    df = data_service.national_trend(days=days)
    out = df.copy()
    out["date"] = out["date"].astype(str)
    return out.to_dict(orient="records")
