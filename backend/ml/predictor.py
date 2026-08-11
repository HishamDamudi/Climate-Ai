import os
import joblib
import numpy as np
import pandas as pd
from datetime import datetime

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl")

SEVERITY_TO_RISK = {
    "Normal": "Low",
    "Alert": "Low",
    "Moderate Heatwave": "Moderate",
    "Severe Heatwave": "High",
    "Extreme Heatwave": "Extreme",
}

SEVERITY_TO_COLOR = {
    "Normal": "Green",
    "Alert": "Yellow",
    "Moderate Heatwave": "Orange",
    "Severe Heatwave": "Red",
    "Extreme Heatwave": "Extreme",
}


class Predictor:
    def __init__(self):
        self._bundle = None

    def _ensure_loaded(self):
        if self._bundle is None:
            if not os.path.exists(MODEL_PATH):
                raise RuntimeError(
                    "Model not found. Run `python ml/train.py` from the backend/ "
                    "directory once to train and cache the model bundle."
                )
            self._bundle = joblib.load(MODEL_PATH)

    @property
    def metrics(self):
        self._ensure_loaded()
        return self._bundle["metrics"]

    def predict(self, district_row: dict, max_temp: float, humidity: float,
                wind_kmph: float, rainfall_mm: float = 0.0):
        self._ensure_loaded()
        b = self._bundle
        day_of_year = datetime.now().timetuple().tm_yday
        X = pd.DataFrame([{
            "max_temp": max_temp,
            "humidity": humidity,
            "wind_kmph": wind_kmph,
            "rainfall_mm": rainfall_mm,
            "lat": district_row["lat"],
            "lon": district_row["lon"],
            "day_of_year": day_of_year,
        }])[b["features"]]

        cls_probs = b["classifier"].predict_proba(X)[0]
        cls_idx = int(np.argmax(cls_probs))
        severity = b["label_encoder"].inverse_transform([cls_idx])[0]
        confidence = float(round(cls_probs[cls_idx], 3))

        expected_temp = float(round(b["regressor"].predict(X)[0], 1))

        # probability of *any* heatwave (moderate or worse)
        classes = list(b["label_encoder"].classes_)
        hw_prob = float(sum(
            p for c, p in zip(classes, cls_probs)
            if c in ("Moderate Heatwave", "Severe Heatwave", "Extreme Heatwave")
        ))

        explanation = self._explain(severity, max_temp, humidity, district_row)

        return {
            "risk_level": SEVERITY_TO_RISK[severity],
            "heatwave_probability": round(hw_prob, 3),
            "expected_temp": expected_temp,
            "severity": severity,
            "confidence_score": confidence,
            "explanation": explanation,
        }

    @staticmethod
    def _explain(severity, max_temp, humidity, district_row):
        region = district_row.get("region", "the region")
        if severity == "Normal":
            return (f"Forecast max temperature of {max_temp}\u00b0C for "
                     f"{district_row.get('district', 'the district')} is within the "
                     f"typical range for {region}; no unusual heat stress indicated.")
        if severity == "Alert":
            return (f"Temperature is trending above the seasonal normal for {region}. "
                     f"Continued monitoring advised; conditions do not yet meet heatwave criteria.")
        base = (f"Forecast max temperature {max_temp}\u00b0C combined with humidity "
                f"{humidity}% exceeds the regional heatwave threshold for {region}.")
        if severity == "Moderate Heatwave":
            return base + " Vulnerable groups should limit midday outdoor exposure."
        if severity == "Severe Heatwave":
            return base + " Significant public-health risk; local advisories recommended."
        return base + " Extreme heat stress expected; emergency response protocols recommended."


predictor = Predictor()
