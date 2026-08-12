"""
API/integration tests for the Climate Intelligence & Heatwave Monitoring System
backend. Uses FastAPI's TestClient (backed by httpx) so no live server needs
to be running - pytest boots the app in-process.

Run from backend/:  pytest tests/test_api.py -v
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import io
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestHealthAndRoot:
    def test_health_check(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_root_returns_api_metadata(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "name" in resp.json()


class TestAuth:
    def test_login_success(self):
        resp = client.post("/auth/login", json={"username": "admin", "password": "climate123"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["role"] == "admin"
        assert "token" in body

    def test_login_wrong_password_returns_401(self):
        resp = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
        assert resp.status_code == 401

    def test_login_unknown_user_returns_401(self):
        resp = client.post("/auth/login", json={"username": "nobody", "password": "x"})
        assert resp.status_code == 401


class TestWeatherRoutes:
    def test_get_all_weather_returns_list(self):
        resp = client.get("/weather")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "max_temp" in data[0]

    def test_get_weather_for_specific_district(self):
        resp = client.get("/weather", params={"district": "Mumbai"})
        assert resp.status_code == 200
        data = resp.json()
        assert all(d["district"] == "Mumbai" for d in data)

    def test_get_weather_for_unknown_district_returns_404(self):
        resp = client.get("/weather", params={"district": "Nowhereville"})
        assert resp.status_code == 404

    def test_national_summary_has_expected_fields(self):
        resp = client.get("/weather/national-summary")
        assert resp.status_code == 200
        body = resp.json()
        for key in ("avg_max_temp", "avg_humidity", "avg_aqi", "districts_monitored"):
            assert key in body


class TestDistrictRoutes:
    def test_list_districts(self):
        resp = client.get("/districts")
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_district_history(self):
        resp = client.get("/districts/Pune/history", params={"days": 5})
        assert resp.status_code == 200
        assert len(resp.json()) <= 5

    def test_district_history_unknown_district_404(self):
        resp = client.get("/districts/Atlantis/history")
        assert resp.status_code == 404

    def test_region_summary(self):
        resp = client.get("/districts/regions/summary")
        assert resp.status_code == 200
        assert len(resp.json()) > 0


class TestPredictionRoutes:
    def test_prediction_for_all_districts(self):
        resp = client.get("/prediction")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) > 0
        assert "risk_level" in data[0]

    def test_single_prediction_valid_district(self):
        resp = client.post("/prediction", json={
            "district": "Jodhpur", "max_temp": 46.0, "humidity": 20, "wind_kmph": 8, "rainfall_mm": 0,
        })
        assert resp.status_code == 200
        body = resp.json()
        assert body["district"] == "Jodhpur"
        assert body["risk_level"] in {"Low", "Moderate", "High", "Extreme"}

    def test_single_prediction_unknown_district_404(self):
        resp = client.post("/prediction", json={
            "district": "Nowhereville", "max_temp": 40, "humidity": 30, "wind_kmph": 10, "rainfall_mm": 0,
        })
        assert resp.status_code == 404

    def test_prediction_missing_field_returns_422(self):
        resp = client.post("/prediction", json={"district": "Pune", "max_temp": 40})
        assert resp.status_code == 422

    def test_model_metrics_reports_scores(self):
        resp = client.get("/prediction/model-metrics")
        assert resp.status_code == 200
        body = resp.json()
        assert "classifier_accuracy" in body
        assert 0 <= body["classifier_accuracy"] <= 1


class TestAlertsRoutes:
    def test_alerts_default_returns_list(self):
        resp = client.get("/alerts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_alerts_min_level_green_returns_at_least_as_many_as_yellow(self):
        green = client.get("/alerts", params={"min_level": "Green"}).json()
        yellow = client.get("/alerts", params={"min_level": "Yellow"}).json()
        assert len(green) >= len(yellow)


class TestHistoryRoute:
    def test_national_trend_default_window(self):
        resp = client.get("/history")
        assert resp.status_code == 200
        assert len(resp.json()) > 0

    def test_national_trend_rejects_out_of_range_days(self):
        resp = client.get("/history", params={"days": 1})  # below ge=7 constraint
        assert resp.status_code == 422


class TestUploadRoute:
    def test_upload_rejects_non_csv_non_xlsx(self):
        resp = client.post(
            "/upload",
            files={"file": ("data.txt", io.BytesIO(b"hello"), "text/plain")},
        )
        assert resp.status_code == 400

    def test_upload_valid_csv_is_imported(self):
        csv_content = (
            "date,district,state,region,lat,lon,max_temp,humidity,wind_kmph,rainfall_mm\n"
            "2026-06-15,Mumbai,Maharashtra,West,19.076,72.8777,39.5,60,14,0\n"
        )
        resp = client.post(
            "/upload",
            files={"file": ("weather.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["rows_imported"] == 1
        assert body["rows_rejected"] == 0

    def test_upload_rejects_unknown_district(self):
        csv_content = (
            "date,district,state,region,lat,lon,max_temp,humidity,wind_kmph,rainfall_mm\n"
            "2026-06-15,Atlantis,Nowhere,West,0,0,39.5,60,14,0\n"
        )
        resp = client.post(
            "/upload",
            files={"file": ("weather.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["rows_imported"] == 0
        assert body["rows_rejected"] == 1
        assert len(body["errors"]) == 1

    def test_upload_missing_required_column_returns_422(self):
        csv_content = "district,max_temp\nMumbai,39.5\n"
        resp = client.post(
            "/upload",
            files={"file": ("weather.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert resp.status_code == 422
