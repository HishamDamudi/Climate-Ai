import io
import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from models.schemas import UploadResult
from services.data_service import data_service
from services import mongo_service
from utils.security import is_suspicious

router = APIRouter(tags=["records"])

REQUIRED_COLUMNS = {"date", "district", "state", "region", "lat", "lon",
                    "max_temp", "humidity", "wind_kmph", "rainfall_mm"}

# Free-text columns get an injection-pattern check in addition to the
# "must match a known district" allowlist check below - defense in depth,
# and it's what the security-testing lab exercises against.
TEXT_COLUMNS = ("district", "state", "region")

VALID_DISTRICTS = None  # populated lazily to avoid circular import at startup


def _valid_districts():
    global VALID_DISTRICTS
    if VALID_DISTRICTS is None:
        VALID_DISTRICTS = set(data_service.districts["district"].str.lower())
    return VALID_DISTRICTS


@router.post("/upload", response_model=UploadResult)
async def upload_weather_file(file: UploadFile = File(...)):
    filename = file.filename or "upload"
    if not (filename.lower().endswith(".csv") or filename.lower().endswith(".xlsx")):
        raise HTTPException(status_code=400, detail="Only .csv and .xlsx files are supported")

    raw = await file.read()
    try:
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(io.BytesIO(raw))
        else:
            df = pd.read_excel(io.BytesIO(raw))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse file: {e}")

    df.columns = [c.strip().lower() for c in df.columns]
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"Missing required column(s): {', '.join(sorted(missing))}. "
                   f"Required: {', '.join(sorted(REQUIRED_COLUMNS))}",
        )

    errors = []
    valid_rows = []
    valid_districts = _valid_districts()
    for i, row in df.iterrows():
        row_errors = []

        # Injection-pattern check on every free-text cell, independent of
        # whether the value happens to also fail the allowlist check below -
        # this is what catches e.g. a district cell containing
        # "Mumbai'; DROP TABLE districts; --" even if that string alone
        # wouldn't match a known district anyway.
        for col in TEXT_COLUMNS:
            cell = str(row.get(col, ""))
            if is_suspicious(cell):
                row_errors.append(f"row {i+2}: '{col}' contains a disallowed pattern")

        if str(row["district"]).lower() not in valid_districts:
            row_errors.append(f"row {i+2}: unknown district '{row['district']}'")
        try:
            float(row["max_temp"]); float(row["humidity"])
            float(row["wind_kmph"]); float(row["rainfall_mm"])
        except (ValueError, TypeError):
            row_errors.append(f"row {i+2}: non-numeric weather value(s)")
        try:
            pd.to_datetime(row["date"])
        except Exception:
            row_errors.append(f"row {i+2}: invalid date '{row['date']}'")

        if row_errors:
            errors.extend(row_errors)
        else:
            valid_rows.append(row)

    imported = 0
    if valid_rows:
        clean_df = pd.DataFrame(valid_rows)
        data_service.append_uploaded(clean_df)

        # Persist to MongoDB too. insert_uploaded_record() type-coerces
        # every field itself, so even though these rows already passed
        # validation above, Mongo never sees a raw, un-typed client value.
        for _, row in clean_df.iterrows():
            try:
                mongo_service.insert_uploaded_record(row.to_dict())
            except ValueError as e:
                errors.append(f"mongo: {e}")
                continue
            imported += 1

    return UploadResult(
        filename=filename,
        rows_received=len(df),
        rows_imported=imported,
        rows_rejected=len(df) - imported,
        errors=errors[:50],  # cap to keep response light
    )


@router.get("/uploads")
def list_uploaded_records(limit: int = 200):
    """Records persisted to MongoDB by the /upload endpoint."""
    return {
        "backend": "mongomock (in-memory fallback)" if mongo_service.is_mock() else "mongodb",
        "count": mongo_service.count_uploaded_records(),
        "records": mongo_service.get_uploaded_records(limit=limit),
    }


@router.delete("/uploads/{record_id}")
def delete_uploaded_mongo_record(record_id: str):
    deleted = mongo_service.delete_uploaded_record(record_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found")
    return {"status": "deleted", "id": record_id}


@router.put("/update")
def update_record(payload: dict = Body(...)):
    """Appends/overwrites a single-day district record (demo-scope: in-memory)."""
    required = REQUIRED_COLUMNS
    missing = required - set(payload.keys())
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing field(s): {', '.join(missing)}")
    for col in TEXT_COLUMNS:
        if is_suspicious(str(payload.get(col, ""))):
            raise HTTPException(status_code=400, detail=f"'{col}' contains a disallowed pattern")
    data_service.append_uploaded(pd.DataFrame([payload]))
    return {"status": "updated", "district": payload["district"], "date": payload["date"]}


@router.delete("/record")
def delete_record(district: str, date: str):
    """Removes an uploaded (in-memory) record; base historical dataset is immutable."""
    if data_service._uploaded_history is None or data_service._uploaded_history.empty:
        raise HTTPException(status_code=404, detail="No uploaded records to delete")
    df = data_service._uploaded_history
    mask = (df["district"].str.lower() == district.lower()) & (df["date"].astype(str) == date)
    if not mask.any():
        raise HTTPException(status_code=404, detail="Record not found among uploaded records")
    data_service._uploaded_history = df[~mask].reset_index(drop=True)
    return {"status": "deleted", "district": district, "date": date}
