from fastapi import APIRouter, HTTPException
from models.schemas import PredictionRequest, PredictionResponse
from services.data_service import data_service
from ml.predictor import predictor

router = APIRouter(prefix="/prediction", tags=["prediction"])


@router.get("")
def prediction_for_all():
    """Runs the trained model against the latest snapshot for every district."""
    snap = data_service.latest_snapshot()
    districts = data_service.districts.set_index("district")
    results = []
    for _, row in snap.iterrows():
        d_meta = districts.loc[row["district"]]
        r = predictor.predict(
            {"lat": row["lat"], "lon": row["lon"], "region": row["region"], "district": row["district"]},
            max_temp=row["max_temp"], humidity=row["humidity"],
            wind_kmph=row["wind_kmph"], rainfall_mm=row["rainfall_mm"],
        )
        r["district"] = row["district"]
        r["state"] = row["state"]
        r["lat"] = float(row["lat"])
        r["lon"] = float(row["lon"])
        r["population_at_risk"] = int(d_meta["population"] * (0.15 if r["risk_level"] != "Low" else 0.01))
        results.append(r)
    return results


@router.get("/model-metrics")
def model_metrics():
    return predictor.metrics


@router.post("", response_model=PredictionResponse)
def predict(req: PredictionRequest):
    districts = data_service.districts.set_index("district")
    if req.district not in districts.index:
        raise HTTPException(status_code=404, detail=f"Unknown district '{req.district}'")
    d = districts.loc[req.district]
    result = predictor.predict(
        {"lat": d["lat"], "lon": d["lon"], "region": d["region"], "district": req.district},
        max_temp=req.max_temp, humidity=req.humidity,
        wind_kmph=req.wind_kmph, rainfall_mm=req.rainfall_mm,
    )
    result["district"] = req.district
    return result
