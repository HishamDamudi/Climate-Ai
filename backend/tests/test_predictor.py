"""
Unit tests for ml/predictor.py — the trained heatwave severity/temperature model.

Requires the model bundle to exist: run `python ml/train.py` once before
running these tests (see backend/README or the project README).

Run from backend/:  pytest tests/test_predictor.py -v
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from ml.predictor import predictor, SEVERITY_TO_RISK, SEVERITY_TO_COLOR

SAMPLE_DISTRICT = {"lat": 26.24, "lon": 73.02, "region": "Northwest", "district": "Jodhpur"}


@pytest.fixture(scope="module", autouse=True)
def ensure_model_available():
    if not os.path.exists(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "model.pkl")):
        pytest.skip("model.pkl not found — run `python ml/train.py` first")


class TestPredictorOutputShape:
    def test_predict_returns_all_expected_keys(self):
        result = predictor.predict(SAMPLE_DISTRICT, max_temp=38, humidity=40, wind_kmph=12, rainfall_mm=0)
        expected_keys = {"risk_level", "heatwave_probability", "expected_temp", "severity", "confidence_score", "explanation"}
        assert expected_keys.issubset(result.keys())

    def test_risk_level_is_valid_category(self):
        result = predictor.predict(SAMPLE_DISTRICT, max_temp=38, humidity=40, wind_kmph=12, rainfall_mm=0)
        assert result["risk_level"] in {"Low", "Moderate", "High", "Extreme"}

    def test_severity_is_valid_category(self):
        result = predictor.predict(SAMPLE_DISTRICT, max_temp=38, humidity=40, wind_kmph=12, rainfall_mm=0)
        assert result["severity"] in {"Normal", "Alert", "Moderate Heatwave", "Severe Heatwave", "Extreme Heatwave"}

    def test_probability_and_confidence_are_bounded(self):
        result = predictor.predict(SAMPLE_DISTRICT, max_temp=38, humidity=40, wind_kmph=12, rainfall_mm=0)
        assert 0.0 <= result["heatwave_probability"] <= 1.0
        assert 0.0 <= result["confidence_score"] <= 1.0

    def test_explanation_is_nonempty_string(self):
        result = predictor.predict(SAMPLE_DISTRICT, max_temp=38, humidity=40, wind_kmph=12, rainfall_mm=0)
        assert isinstance(result["explanation"], str)
        assert len(result["explanation"]) > 0


class TestPredictorBehaviour:
    """Sanity checks on model behaviour, not just output shape - a model that
    flags extreme heat as 'Normal' should fail these even if the shape is fine."""

    def test_extreme_temperature_is_flagged_as_high_or_extreme_risk(self):
        result = predictor.predict(SAMPLE_DISTRICT, max_temp=48, humidity=15, wind_kmph=5, rainfall_mm=0)
        assert result["risk_level"] in {"High", "Extreme"}

    def test_mild_temperature_is_flagged_as_low_risk(self):
        result = predictor.predict(SAMPLE_DISTRICT, max_temp=24, humidity=50, wind_kmph=15, rainfall_mm=5)
        assert result["risk_level"] == "Low"

    def test_severity_to_risk_mapping_is_monotonic(self):
        order = ["Normal", "Alert", "Moderate Heatwave", "Severe Heatwave", "Extreme Heatwave"]
        risk_rank = {"Low": 0, "Moderate": 1, "High": 2, "Extreme": 3}
        ranks = [risk_rank[SEVERITY_TO_RISK[s]] for s in order]
        assert ranks == sorted(ranks), "risk level should never decrease as severity increases"

    def test_higher_temperature_does_not_decrease_heatwave_probability(self):
        cooler = predictor.predict(SAMPLE_DISTRICT, max_temp=30, humidity=40, wind_kmph=12, rainfall_mm=0)
        hotter = predictor.predict(SAMPLE_DISTRICT, max_temp=46, humidity=40, wind_kmph=12, rainfall_mm=0)
        assert hotter["heatwave_probability"] >= cooler["heatwave_probability"]


class TestSeverityColorMapping:
    def test_all_severities_have_a_color(self):
        severities = ["Normal", "Alert", "Moderate Heatwave", "Severe Heatwave", "Extreme Heatwave"]
        for s in severities:
            assert s in SEVERITY_TO_COLOR

    def test_extreme_heatwave_maps_to_extreme_color(self):
        assert SEVERITY_TO_COLOR["Extreme Heatwave"] == "Extreme"
