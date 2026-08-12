"""
Unit tests for services/data_service.py

Covers the pure calculation functions (heat_index, derive_aqi, derive_uv) and
the DataService class's data-loading and query behaviour.

Run from backend/:  pytest tests/test_data_service.py -v
"""
import sys
import os
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_service import heat_index, derive_aqi, derive_uv, DataService


# ---------------------------------------------------------------------------
# heat_index()
# ---------------------------------------------------------------------------

class TestHeatIndex:
    def test_returns_float(self):
        result = heat_index(temp_c=35, humidity=60)
        assert isinstance(result, float)

    def test_high_temp_high_humidity_increases_heat_index(self):
        """Heat index should exceed the raw air temperature under humid heat."""
        result = heat_index(temp_c=35, humidity=70)
        assert result > 35

    def test_known_reference_value(self):
        """32C at 70% humidity is a commonly cited heat-index reference point
        (~41C 'feels like') - assert within a reasonable tolerance."""
        result = heat_index(temp_c=32, humidity=70)
        assert 38 <= result <= 44

    def test_low_humidity_stays_closer_to_actual_temp(self):
        humid_case = heat_index(temp_c=35, humidity=80)
        dry_case = heat_index(temp_c=35, humidity=20)
        assert humid_case > dry_case


# ---------------------------------------------------------------------------
# derive_aqi()
# ---------------------------------------------------------------------------

class TestDeriveAqi:
    @pytest.mark.parametrize("region", ["North", "West", "South", "Northeast", "Unknown"])
    def test_returns_int_within_valid_range(self, region):
        result = derive_aqi(region, day_of_year=180)
        assert isinstance(result, int)
        assert 20 <= result <= 400

    def test_unknown_region_falls_back_to_default_base(self):
        # "Unknown" isn't in the lookup table, should not raise and should
        # still return a sane value using the default base (100).
        result = derive_aqi("Unknown", day_of_year=1)
        assert 20 <= result <= 400

    def test_north_region_has_higher_base_than_northeast(self):
        # North's base (180) is set higher than Northeast's (70) in the model
        north = derive_aqi("North", day_of_year=1)
        northeast = derive_aqi("Northeast", day_of_year=1)
        assert north > northeast


# ---------------------------------------------------------------------------
# derive_uv()
# ---------------------------------------------------------------------------

class TestDeriveUv:
    def test_higher_temp_gives_higher_uv(self):
        low = derive_uv(max_temp=25)
        high = derive_uv(max_temp=45)
        assert high > low

    def test_uv_is_clipped_to_valid_range(self):
        assert 0 <= derive_uv(max_temp=-10) <= 12
        assert 0 <= derive_uv(max_temp=100) <= 12


# ---------------------------------------------------------------------------
# DataService
# ---------------------------------------------------------------------------

class TestDataService:
    @pytest.fixture
    def service(self):
        return DataService()

    def test_districts_loads_expected_columns(self, service):
        df = service.districts
        assert {"district", "state", "region", "lat", "lon", "population"}.issubset(df.columns)
        assert len(df) > 0

    def test_history_has_derived_columns(self, service):
        df = service.history
        assert {"heat_index", "aqi", "uv_index"}.issubset(df.columns)

    def test_latest_snapshot_returns_one_row_per_district(self, service):
        snap = service.latest_snapshot()
        assert snap["district"].is_unique

    def test_district_series_filters_correctly(self, service):
        any_district = service.districts.iloc[0]["district"]
        series = service.district_series(any_district, days=10)
        assert (series["district"] == any_district).all()
        assert len(series) <= 10

    def test_district_series_unknown_district_is_empty(self, service):
        series = service.district_series("Nonexistent City", days=10)
        assert series.empty

    def test_append_uploaded_extends_history(self, service):
        before = len(service.history)
        new_row = pd.DataFrame([{
            "date": "2026-06-01", "district": "Mumbai", "state": "Maharashtra",
            "region": "West", "lat": 19.076, "lon": 72.8777,
            "max_temp": 41.0, "humidity": 55.0, "wind_kmph": 10.0, "rainfall_mm": 0.0,
        }])
        service.append_uploaded(new_row)
        after = len(service.history)
        assert after == before + 1
