"""
Generates a synthetic (but realistic-shaped) historical weather dataset for the
Climate Intelligence & Heatwave Monitoring demo. In production this file is
replaced by IMD historical GRD extracts (see documentation/README).

Run: python generate_history.py
Produces: weather_history.csv (365 days x district)
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

districts = pd.read_csv("districts.csv")

REGION_BASE_TEMP = {
    "West": 33, "Central": 34, "Northwest": 36, "North": 32,
    "East": 31, "Northeast": 28, "South": 30,
}

start = datetime(2025, 1, 1)
rows = []
for _, d in districts.iterrows():
    base = REGION_BASE_TEMP.get(d["region"], 32)
    for day in range(365):
        date = start + timedelta(days=day)
        # seasonal curve: peak around day 140-170 (May), trough in Jan
        season = 8 * np.sin((day - 60) / 365 * 2 * np.pi)
        noise = np.random.normal(0, 1.8)
        max_temp = round(base + season + noise, 1)
        humidity = round(np.clip(55 - season * 1.5 + np.random.normal(0, 6), 10, 95), 1)
        wind = round(np.clip(np.random.normal(12, 4), 1, 40), 1)
        rainfall = round(max(0, np.random.exponential(2) - (season if season > 0 else 0)), 1)
        rows.append({
            "date": date.strftime("%Y-%m-%d"),
            "district": d["district"],
            "state": d["state"],
            "region": d["region"],
            "lat": d["lat"],
            "lon": d["lon"],
            "max_temp": max_temp,
            "humidity": humidity,
            "wind_kmph": wind,
            "rainfall_mm": rainfall,
        })

df = pd.DataFrame(rows)
df.to_csv("weather_history.csv", index=False)
print(f"Wrote {len(df)} rows to weather_history.csv")
