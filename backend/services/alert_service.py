from datetime import datetime, timezone
from services.data_service import data_service
from ml.predictor import predictor, SEVERITY_TO_COLOR

RECOMMENDED_ACTIONS = {
    "Green": ["No action required", "Stay updated on forecasts"],
    "Yellow": ["Stay hydrated", "Avoid strenuous activity during midday"],
    "Orange": ["Limit outdoor exposure 12pm-3pm", "Check on elderly/at-risk neighbours",
               "Keep ORS/water accessible"],
    "Red": ["Avoid outdoor activity during peak hours", "Local authorities to open cooling centers",
            "Hospitals to prepare for heat-illness cases"],
    "Extreme": ["Issue public emergency advisory", "Suspend outdoor labour/school activity as needed",
                "Activate disaster management protocols"],
}

_next_id = 1


def _severity_rank(color: str) -> int:
    order = ["Green", "Yellow", "Orange", "Red", "Extreme"]
    return order.index(color) if color in order else 0


def generate_alerts(min_level: str = "Yellow"):
    """Runs the prediction model against the latest snapshot for every district
    and returns an alert for any district at or above `min_level` severity."""
    global _next_id
    snapshot = data_service.latest_snapshot()
    districts = data_service.districts.set_index("district")
    alerts = []
    min_rank = _severity_rank(min_level)

    for _, row in snapshot.iterrows():
        d_meta = districts.loc[row["district"]]
        result = predictor.predict(
            {"lat": row["lat"], "lon": row["lon"], "region": row["region"], "district": row["district"]},
            max_temp=row["max_temp"], humidity=row["humidity"],
            wind_kmph=row["wind_kmph"], rainfall_mm=row["rainfall_mm"],
        )
        color = SEVERITY_TO_COLOR[result["severity"]]
        if _severity_rank(color) < min_rank:
            continue
        alerts.append({
            "id": _next_id,
            "level": color,
            "title": f"{result['severity']} — {row['district']}, {row['state']}",
            "description": result["explanation"],
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "affected_areas": [f"{row['district']}, {row['state']}"],
            "recommended_actions": RECOMMENDED_ACTIONS.get(color, []),
        })
        _next_id += 1

    alerts.sort(key=lambda a: _severity_rank(a["level"]), reverse=True)
    return alerts
