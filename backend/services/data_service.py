"""
Central data-access layer. Loads district metadata + historical weather from
CSV/Excel (Phase I: Meteorological Data Acquisition). Designed so the storage
backend can later be swapped for PostgreSQL/PostGIS without touching callers.
"""
import os
import numpy as np
import pandas as pd
from functools import lru_cache
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")

DISTRICTS_PATH = os.path.join(DATASETS_DIR, "districts.csv")
HISTORY_PATH = os.path.join(DATASETS_DIR, "weather_history.csv")


def heat_index(temp_c: float, humidity: float) -> float:
    """Simplified Rothfusz heat-index approximation (Celsius)."""
    t = temp_c * 9 / 5 + 32  # to Fahrenheit
    rh = humidity
    hi = (
        -42.379 + 2.04901523 * t + 10.14333127 * rh
        - 0.22475541 * t * rh - 0.00683783 * t * t
        - 0.05481717 * rh * rh + 0.00122874 * t * t * rh
        + 0.00085282 * t * rh * rh - 0.00000199 * t * t * rh * rh
    )
    return round((hi - 32) * 5 / 9, 1)  # back to Celsius


def derive_aqi(region: str, day_of_year: int) -> int:
    """Deterministic pseudo-AQI derived from region + season (placeholder for
    a real air-quality feed)."""
    base = {"North": 180, "Northwest": 150, "Central": 130, "West": 110,
            "East": 120, "South": 90, "Northeast": 70}.get(region, 100)
    seasonal = 40 * np.sin((day_of_year - 300) / 365 * 2 * np.pi)
    return int(np.clip(base + seasonal, 20, 400))


def derive_uv(max_temp: float) -> float:
    return round(np.clip(4 + (max_temp - 25) * 0.35, 0, 12), 1)


class DataService:
    def __init__(self):
        self._districts = None
        self._history = None
        self._uploaded_history = None  # admin-uploaded records, kept separate

    # ---------- loaders ----------
    @property
    def districts(self) -> pd.DataFrame:
        if self._districts is None:
            self._districts = pd.read_csv(DISTRICTS_PATH)
        return self._districts

    @property
    def history(self) -> pd.DataFrame:
        if self._history is None:
            df = pd.read_csv(HISTORY_PATH, parse_dates=["date"])
            df["doy"] = df["date"].dt.dayofyear
            df["heat_index"] = df.apply(
                lambda r: heat_index(r["max_temp"], r["humidity"]), axis=1
            )
            df["aqi"] = df.apply(lambda r: derive_aqi(r["region"], r["doy"]), axis=1)
            df["uv_index"] = df["max_temp"].apply(derive_uv)
            self._history = df
        if self._uploaded_history is not None and len(self._uploaded_history):
            return pd.concat([self._history, self._uploaded_history], ignore_index=True)
        return self._history

    def append_uploaded(self, df: pd.DataFrame):
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["doy"] = df["date"].dt.dayofyear
        df["heat_index"] = df.apply(lambda r: heat_index(r["max_temp"], r["humidity"]), axis=1)
        df["aqi"] = df.apply(lambda r: derive_aqi(r["region"], r["doy"]), axis=1)
        df["uv_index"] = df["max_temp"].apply(derive_uv)
        self._uploaded_history = (
            df if self._uploaded_history is None
            else pd.concat([self._uploaded_history, df], ignore_index=True)
        )

    # ---------- queries ----------
    def latest_snapshot(self) -> pd.DataFrame:
        h = self.history
        idx = h.groupby("district")["date"].idxmax()
        return h.loc[idx].sort_values("district").reset_index(drop=True)

    def district_series(self, district: str, days: int = 60) -> pd.DataFrame:
        h = self.history
        sub = h[h["district"].str.lower() == district.lower()].sort_values("date")
        return sub.tail(days)

    def region_summary(self) -> pd.DataFrame:
        snap = self.latest_snapshot()
        return snap.groupby("region").agg(
            avg_max_temp=("max_temp", "mean"),
            avg_humidity=("humidity", "mean"),
            avg_aqi=("aqi", "mean"),
            districts=("district", "count"),
        ).round(1).reset_index()

    def national_trend(self, days: int = 90) -> pd.DataFrame:
        h = self.history
        recent_dates = sorted(h["date"].unique())[-days:]
        sub = h[h["date"].isin(recent_dates)]
        return sub.groupby("date").agg(
            avg_max_temp=("max_temp", "mean"),
            avg_humidity=("humidity", "mean"),
            avg_rainfall=("rainfall_mm", "mean"),
            avg_aqi=("aqi", "mean"),
        ).round(2).reset_index()


data_service = DataService()
