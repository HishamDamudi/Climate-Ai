"""
Phase II: AI-Driven Heatwave Analytics and Prediction.

Trains two lightweight models on the historical dataset:
  1. RandomForestRegressor  -> next-day expected max temperature
  2. RandomForestClassifier -> heatwave severity class

Severity labels are derived using an IMD-style rule (departure from the
region's climatological normal + absolute threshold) so the classifier learns
a smoothed, generalizable version of that rule across regions/seasons.

Run: python train.py   (writes model.pkl next to this file)
"""
import os
import sys
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.data_service import data_service, heat_index  # noqa: E402

MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.pkl")

SEVERITY_ORDER = ["Normal", "Alert", "Moderate Heatwave", "Severe Heatwave", "Extreme Heatwave"]


def label_severity(row, region_normal):
    departure = row["max_temp"] - region_normal
    if row["max_temp"] >= 47 or departure >= 8:
        return "Extreme Heatwave"
    if row["max_temp"] >= 45 or departure >= 6.4:
        return "Severe Heatwave"
    if row["max_temp"] >= 40 or departure >= 4.5:
        return "Moderate Heatwave"
    if departure >= 2.5:
        return "Alert"
    return "Normal"


def build_training_frame():
    df = data_service.history.copy()
    normals = df.groupby("region")["max_temp"].transform("mean")
    df["region_normal"] = normals
    df["severity"] = df.apply(lambda r: label_severity(r, r["region_normal"]), axis=1)
    df["month"] = df["date"].dt.month
    df["day_of_year"] = df["date"].dt.dayofyear
    return df


def main():
    df = build_training_frame()

    features = ["max_temp", "humidity", "wind_kmph", "rainfall_mm", "lat", "lon", "day_of_year"]
    X = df[features]

    # --- classifier: severity ---
    le = LabelEncoder()
    le.fit(SEVERITY_ORDER)
    y_cls = le.transform(df["severity"])
    Xc_train, Xc_test, yc_train, yc_test = train_test_split(
        X, y_cls, test_size=0.2, random_state=42, stratify=y_cls
    )
    clf = RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, class_weight="balanced")
    clf.fit(Xc_train, yc_train)
    cls_acc = clf.score(Xc_test, yc_test)

    # --- regressor: next-day max temp (use same-day features shifted by district) ---
    df_sorted = df.sort_values(["district", "date"])
    df_sorted["next_max_temp"] = df_sorted.groupby("district")["max_temp"].shift(-1)
    reg_df = df_sorted.dropna(subset=["next_max_temp"])
    Xr = reg_df[features]
    yr = reg_df["next_max_temp"]
    Xr_train, Xr_test, yr_train, yr_test = train_test_split(Xr, yr, test_size=0.2, random_state=42)
    reg = RandomForestRegressor(n_estimators=200, max_depth=12, random_state=42)
    reg.fit(Xr_train, yr_train)
    reg_r2 = reg.score(Xr_test, yr_test)

    joblib.dump({
        "classifier": clf,
        "regressor": reg,
        "label_encoder": le,
        "features": features,
        "metrics": {"classifier_accuracy": round(cls_acc, 3), "regressor_r2": round(reg_r2, 3)},
    }, MODEL_PATH)

    print(f"Classifier accuracy: {cls_acc:.3f}")
    print(f"Regressor R^2:       {reg_r2:.3f}")
    print(f"Saved model bundle -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
