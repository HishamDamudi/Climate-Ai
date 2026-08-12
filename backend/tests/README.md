# Test Suite — Climate Intelligence & Heatwave Monitoring System

PyTest unit + API tests for the FastAPI backend. 56 tests, ~77% statement
coverage across `services/`, `ml/`, and `routes/`.

## Setup

```bash
cd backend
pip install -r requirements.txt --break-system-packages
pip install -r requirements-test.txt --break-system-packages
cd ml && python3 train.py && cd ..     # generates model.pkl - required by test_predictor.py
```

## Run everything

```bash
pytest tests/ -v
```

## Run with coverage

```bash
pytest tests/ --cov=services --cov=ml --cov=routes --cov-report=term-missing
```

## Run a single file / test

```bash
pytest tests/test_predictor.py -v
pytest tests/test_api.py::TestPredictionRoutes::test_single_prediction_valid_district -v
```

## What's covered

| File | What it tests |
|---|---|
| `test_data_service.py` | Pure calculation functions (`heat_index`, `derive_aqi`, `derive_uv`) and the `DataService` data-loading/query layer — unit tests, no HTTP involved. |
| `test_predictor.py` | The trained ML model wrapper: output shape/types, valid category values, bounded probabilities, and **behavioural** sanity checks (e.g. extreme temperatures must be flagged as high/extreme risk, not just "some string came back"). |
| `test_api.py` | End-to-end API tests via FastAPI's `TestClient` — every route (`/weather`, `/districts`, `/prediction`, `/alerts`, `/history`, `/upload`, `/auth`) including success paths, 404s for unknown districts, 422s for bad input, and file-upload validation. |

## Notes for the lab report

- `test_predictor.py` is skipped automatically (not failed) if `model.pkl`
  hasn't been generated yet — the fixture checks for the file and calls
  `pytest.skip(...)` with a clear message rather than erroring.
- Tests are grouped into classes (`TestHeatIndex`, `TestPredictorBehaviour`,
  etc.) so `pytest -v` output reads as a readable spec — good for a results
  screenshot.
- `TestPredictorBehaviour` is the interesting one to highlight in your
  write-up: it doesn't just check "did the function return without
  crashing" — it checks the model's actual heatwave judgement is sane
  (mild weather → Low risk, extreme heat → High/Extreme risk, warmer
  input never lowers heatwave probability).
