from fastapi import APIRouter, Query
from typing import Optional
from services.alert_service import generate_alerts

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("")
def get_alerts(min_level: Optional[str] = Query("Yellow"), search: Optional[str] = None):
    alerts = generate_alerts(min_level=min_level)
    if search:
        s = search.lower()
        alerts = [a for a in alerts if s in a["title"].lower() or
                  any(s in area.lower() for area in a["affected_areas"])]
    return alerts
