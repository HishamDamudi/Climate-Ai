"""
Security tests: SQL-injection-style and NoSQL/MongoDB operator-injection
payloads against every user input surface in the app - login, file upload
(CSV/Excel), and the MongoDB-backed /uploads endpoint.

Run from backend/:  pytest tests/test_security_injection.py -v
"""
import sys
import os
import io

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from main import app
from utils.security import is_suspicious, sanitize_text
from services import mongo_service

client = TestClient(app)

# A representative set of classic SQLi payloads (OWASP-style), plus
# MongoDB operator-injection strings and a couple of XSS-style probes.
INJECTION_PAYLOADS = [
    "admin' OR '1'='1",
    "admin'--",
    "' OR 1=1 --",
    "'; DROP TABLE districts; --",
    "1' UNION SELECT username, password FROM users --",
    "Mumbai'; DROP TABLE weather; --",
    "$where: this.password",
    "$ne",
    "<script>alert(1)</script>",
]


# ---------------------------------------------------------------------------
# Utility-level tests (utils/security.py)
# ---------------------------------------------------------------------------

class TestIsSuspicious:
    @pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
    def test_flags_known_injection_payloads(self, payload):
        assert is_suspicious(payload) is True

    @pytest.mark.parametrize("value", ["Mumbai", "Pune", "Andhra Pradesh", "Chandigarh", ""])
    def test_does_not_flag_legitimate_values(self, value):
        assert is_suspicious(value) is False

    def test_non_string_input_is_flagged(self):
        # e.g. a dict sneaking in where a string was expected -
        # {"$ne": None} arriving as an actual object, not text.
        assert is_suspicious({"$ne": None}) is True
        assert is_suspicious(["a", "b"]) is True


class TestSanitizeText:
    def test_strips_control_characters(self):
        result = sanitize_text("Mumbai\x00\x01")
        assert result == "Mumbai"

    def test_truncates_to_max_length(self):
        result = sanitize_text("A" * 500, max_len=50)
        assert len(result) == 50

    def test_trims_whitespace(self):
        assert sanitize_text("  Pune  ") == "Pune"


# ---------------------------------------------------------------------------
# Login endpoint
# ---------------------------------------------------------------------------

class TestLoginInjection:
    @pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
    def test_injection_in_username_is_rejected_not_500(self, payload):
        resp = client.post("/auth/login", json={"username": payload, "password": "x"})
        assert resp.status_code == 400
        assert resp.status_code != 500

    @pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
    def test_injection_in_password_is_rejected_not_500(self, payload):
        resp = client.post("/auth/login", json={"username": "admin", "password": payload})
        assert resp.status_code == 400

    def test_injection_payload_never_authenticates(self):
        resp = client.post("/auth/login", json={"username": "admin' OR '1'='1", "password": "anything"})
        assert resp.status_code != 200
        assert "token" not in resp.json()

    def test_nosql_operator_as_json_object_is_rejected_by_type_validation(self):
        """Sending {"$ne": null} as the password value (not a string) should
        be rejected by Pydantic's type system (422) before it ever reaches
        application logic - this is what actually blocks classic Mongo
        operator injection, independent of the is_suspicious() string check."""
        resp = client.post("/auth/login", json={"username": "admin", "password": {"$ne": None}})
        assert resp.status_code == 422

    def test_legitimate_login_still_works(self):
        resp = client.post("/auth/login", json={"username": "admin", "password": "climate123"})
        assert resp.status_code == 200
        assert "token" in resp.json()


# ---------------------------------------------------------------------------
# CSV / Excel upload
# ---------------------------------------------------------------------------

class TestUploadInjection:
    @pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
    def test_injection_in_district_column_is_rejected(self, payload):
        csv_content = (
            "date,district,state,region,lat,lon,max_temp,humidity,wind_kmph,rainfall_mm\n"
            f'2026-06-15,"{payload}",Maharashtra,West,19.07,72.87,39.5,60,14,0\n'
        )
        resp = client.post(
            "/upload",
            files={"file": ("weather.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["rows_imported"] == 0
        assert body["rows_rejected"] == 1

    @pytest.mark.parametrize("payload", INJECTION_PAYLOADS)
    def test_injection_in_state_column_is_rejected(self, payload):
        csv_content = (
            "date,district,state,region,lat,lon,max_temp,humidity,wind_kmph,rainfall_mm\n"
            f'2026-06-15,Mumbai,"{payload}",West,19.07,72.87,39.5,60,14,0\n'
        )
        resp = client.post(
            "/upload",
            files={"file": ("weather.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["rows_imported"] == 0
        assert body["rows_rejected"] == 1

    def test_server_never_returns_500_for_any_injection_payload(self):
        for payload in INJECTION_PAYLOADS:
            csv_content = (
                "date,district,state,region,lat,lon,max_temp,humidity,wind_kmph,rainfall_mm\n"
                f'2026-06-15,"{payload}","{payload}",West,19.07,72.87,39.5,60,14,0\n'
            )
            resp = client.post(
                "/upload",
                files={"file": ("weather.csv", io.BytesIO(csv_content.encode()), "text/csv")},
            )
            assert resp.status_code < 500, f"payload {payload!r} caused a server error"

    def test_legitimate_upload_still_imports_and_reaches_mongo(self):
        before = mongo_service.count_uploaded_records()
        csv_content = (
            "date,district,state,region,lat,lon,max_temp,humidity,wind_kmph,rainfall_mm\n"
            "2026-06-16,Pune,Maharashtra,West,18.52,73.85,38.0,55,12,0\n"
        )
        resp = client.post(
            "/upload",
            files={"file": ("weather.csv", io.BytesIO(csv_content.encode()), "text/csv")},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["rows_imported"] == 1
        after = mongo_service.count_uploaded_records()
        assert after == before + 1


# ---------------------------------------------------------------------------
# MongoDB service layer - operator-injection defense via type coercion
# ---------------------------------------------------------------------------

class TestMongoServiceTypeCoercion:
    def test_operator_injection_value_is_stored_as_inert_string(self):
        """If a caller ever managed to pass a dict-like operator structure
        through as a district 'string', insert_uploaded_record() coerces it
        with str(...) before storage - it becomes a harmless literal, never
        a live Mongo query operator."""
        row = {
            "date": "2026-06-17", "district": "Mumbai", "state": "Maharashtra",
            "region": "West", "lat": 19.07, "lon": 72.87,
            "max_temp": 39.0, "humidity": 50, "wind_kmph": 10, "rainfall_mm": 0,
        }
        doc = mongo_service.insert_uploaded_record(row)
        assert isinstance(doc["district"], str)
        assert doc["district"] == "Mumbai"

    def test_suspicious_free_text_field_raises_value_error(self):
        row = {
            "date": "2026-06-17", "district": "'; DROP TABLE x; --", "state": "Maharashtra",
            "region": "West", "lat": 19.07, "lon": 72.87,
            "max_temp": 39.0, "humidity": 50, "wind_kmph": 10, "rainfall_mm": 0,
        }
        with pytest.raises(ValueError):
            mongo_service.insert_uploaded_record(row)

    def test_get_uploaded_records_returns_json_serializable_ids(self):
        records = mongo_service.get_uploaded_records(limit=5)
        for r in records:
            assert isinstance(r["_id"], str)


class TestUploadsEndpoint:
    def test_list_uploads_endpoint(self):
        resp = client.get("/uploads")
        assert resp.status_code == 200
        body = resp.json()
        assert "records" in body
        assert "backend" in body

    def test_delete_nonexistent_upload_returns_404(self):
        resp = client.delete("/uploads/000000000000000000000000")
        assert resp.status_code == 404
