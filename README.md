# Climate Intelligence & Heatwave Monitoring System

A full-stack demo implementation of the KJS-CES-01 use case: region-wise heatwave
forecasting, monitoring and early warning, built with a FastAPI + scikit-learn
backend and a React (Vite/Tailwind) dashboard frontend.

## What's included

- **backend/** — FastAPI REST API, data layer, and a trained ML model
  (RandomForest classifier for heatwave severity + regressor for next-day max
  temperature) served from `/prediction`.
- **frontend/** — React dashboard: login, overview cards, interactive Leaflet
  map, Chart.js analytics, alerts, CSV/Excel upload, sortable data table, and
  settings.
- **backend/datasets/** — a synthetically generated but realistically-shaped
  historical dataset (20 districts × 365 days) standing in for the real IMD
  GRD extracts referenced in the use case document. Swap in real IMD data by
  replacing `weather_history.csv` with the same column schema and re-running
  `python ml/train.py`.

This is a working reference implementation, not the final production system —
see "Where this differs from the full brief" below.

## Quick start

### 1. Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt --break-system-packages   # drop the flag in a venv
cd ml && python3 train.py && cd ..                 # trains & caches model.pkl (~5s)
uvicorn main:app --reload --port 8000
```

API docs: http://127.0.0.1:8000/docs

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://127.0.0.1:5173 — the Vite dev server proxies `/api/*` to the
backend on port 8000 (see `vite.config.js`).

### Demo login

| Username | Password    | Role   |
|----------|-------------|--------|
| admin    | climate123  | admin  |
| viewer   | viewer123   | viewer |

## Uploading your own data

The Upload page (or `POST /upload`) accepts `.csv`/`.xlsx` files with columns:
`date, district, state, region, lat, lon, max_temp, humidity, wind_kmph, rainfall_mm`.
District names must match an entry in `backend/datasets/districts.csv`
(edit/extend that file to add more districts).

## Where this differs from the full brief

The original spec (see `documentation/`) describes a much larger system —
PostgreSQL/PostGIS, JWT auth, GIS layers, LLM-based advisory generation, IoT/AWS
ingestion, PDF/Excel report exports, etc. This build focuses on a working,
demoable core:

- **Auth** is a simple in-memory token session (JWT-ready structure, not JWT yet).
- **Storage** is CSV/pandas in-memory, not PostgreSQL/PostGIS (the data-access
  layer in `services/data_service.py` is written so swapping the storage
  backend doesn't require touching route code).
- **ML** is a real trained scikit-learn pipeline, but trained on a synthetic
  historical dataset with IMD-style rule-derived labels rather than genuine
  IMD GRD records (which aren't publicly bundled here).
- **LLM-based advisory generation** and **IoT/AWS ingestion** are out of
  scope for this build; the alerts module produces rule/ML-derived advisories
  instead of LLM-generated stakeholder-specific text.
- **Reports (PDF/Excel export)** are not implemented; CSV export is provided
  on the Alerts and Data Table pages instead.

## Folder structure

```
ClimateAI/
├─ backend/
│  ├─ main.py                 FastAPI app entrypoint
│  ├─ config/settings.py      env-driven config (CORS origins, etc.)
│  ├─ routes/                 weather, districts, prediction, alerts, history, records, auth
│  ├─ services/                data_service.py (CSV data layer), alert_service.py
│  ├─ ml/                     train.py, predictor.py, model.pkl (generated)
│  ├─ models/schemas.py       Pydantic request/response models
│  └─ datasets/               districts.csv, weather_history.csv, generate_history.py
└─ frontend/
   └─ src/
      ├─ pages/               Dashboard, MapView, Analytics, Alerts, Upload, DataTable, Settings, Login
      ├─ components/          Sidebar, Navbar, MetricCard, SeverityBadge, ProtectedRoute
      ├─ context/             ThemeContext, AuthContext
      └─ services/api.js      Axios client + typed API helpers
```
