"""
MongoDB persistence layer for admin-uploaded weather records.

Design choices worth knowing for the security-testing lab:

- `insert_uploaded_record()` NEVER accepts and stores a raw client dict.
  Every field is explicitly coerced to its expected primitive type
  (str/float) before being written to Mongo. This is the actual defense
  against MongoDB operator injection (e.g. a client sending
  `{"district": {"$ne": null}}`) - coercing to `str(...)` turns any such
  payload into the harmless literal string "{'$ne': None}" instead of a
  live query operator.

- If MongoDB isn't reachable (e.g. no MONGODB_URI configured, or running
  in a sandbox/CI without a real cluster), this module transparently falls
  back to `mongomock`, an in-memory drop-in that implements the same
  pymongo API. This keeps local dev, tests, and grading environments
  working with zero setup while still exercising real pymongo query code
  in production against a real cluster (e.g. MongoDB Atlas).
"""
import logging
from datetime import datetime, timezone

from config.settings import MONGODB_URI, MONGODB_DB
from utils.security import is_suspicious, sanitize_text

logger = logging.getLogger("climate_ai.mongo")

_client = None
_using_mock = False


def _get_client():
    global _client, _using_mock
    if _client is not None:
        return _client

    try:
        import pymongo
        candidate = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
        candidate.admin.command("ping")  # forces connection attempt now, not lazily later
        _client = candidate
        _using_mock = False
        logger.info("Connected to MongoDB at %s", MONGODB_URI)
    except Exception as e:
        import mongomock
        logger.warning(
            "MongoDB unreachable (%s) - falling back to in-memory mongomock. "
            "Set MONGODB_URI to a real cluster (e.g. MongoDB Atlas) for persistence.",
            e,
        )
        _client = mongomock.MongoClient()
        _using_mock = True
    return _client


def is_mock() -> bool:
    _get_client()
    return _using_mock


def _collection():
    return _get_client()[MONGODB_DB]["uploaded_weather_records"]


def insert_uploaded_record(row: dict) -> dict:
    """Builds a strictly-typed document from a validated row and inserts it.
    Raises ValueError if a free-text field looks like an injection payload."""
    district = sanitize_text(str(row["district"]))
    state = sanitize_text(str(row["state"]))
    region = sanitize_text(str(row["region"]))

    for field_name, field_value in (("district", district), ("state", state), ("region", region)):
        if is_suspicious(field_value):
            raise ValueError(f"Rejected: '{field_name}' contains a disallowed pattern")

    doc = {
        "date": str(row["date"]),
        "district": district,
        "state": state,
        "region": region,
        "lat": float(row["lat"]),
        "lon": float(row["lon"]),
        "max_temp": float(row["max_temp"]),
        "humidity": float(row["humidity"]),
        "wind_kmph": float(row["wind_kmph"]),
        "rainfall_mm": float(row["rainfall_mm"]),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    result = _collection().insert_one(doc)
    doc["_id"] = str(result.inserted_id)
    return doc


def get_uploaded_records(limit: int = 200) -> list:
    docs = list(_collection().find().sort("uploaded_at", -1).limit(limit))
    for d in docs:
        d["_id"] = str(d["_id"])
    return docs


def delete_uploaded_record(record_id: str) -> bool:
    from bson import ObjectId
    try:
        oid = ObjectId(record_id)
    except Exception:
        return False
    result = _collection().delete_one({"_id": oid})
    return result.deleted_count > 0


def count_uploaded_records() -> int:
    return _collection().count_documents({})
