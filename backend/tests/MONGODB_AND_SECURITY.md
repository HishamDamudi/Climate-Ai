# MongoDB & Injection Testing

## What was added

- **MongoDB persistence** (`services/mongo_service.py`) — every successful
  CSV/Excel upload row is now also written to a `uploaded_weather_records`
  collection in MongoDB, in addition to the existing in-memory pandas store.
  New endpoints: `GET /uploads` (list, newest first) and
  `DELETE /uploads/{id}`.
- **Injection defense** (`utils/security.py`) — a pattern-matching layer
  (`is_suspicious()`) checks every free-text field (district, state, region,
  login username/password) against classic SQL-injection tokens, MongoDB
  operator-injection strings (`$where`, `$ne`, `$gt`, ...), and basic
  script-injection patterns before anything is stored or authenticated
  against.
- **Type-coercion as the real Mongo defense** — `insert_uploaded_record()`
  never writes a raw client dict into MongoDB. Every field is explicitly
  cast to `str`/`float` first, so even if a client somehow got an operator
  structure past validation, it becomes an inert string, not a live query
  operator, by the time it reaches pymongo.
- **`requirements.txt`** now includes `pymongo`; `requirements-test.txt`
  includes `mongomock` so the test suite (and local dev) works without a
  real MongoDB instance.

## Local setup

You do **not** need a real MongoDB running to develop or run the test suite —
if `MONGODB_URI` is unreachable, `mongo_service.py` automatically falls back
to `mongomock` (an in-memory, API-compatible drop-in) and logs a warning.
This is intentional so grading/CI environments never need a live database.

To use a real MongoDB locally:
```bash
docker run -d -p 27017:27017 --name climate-mongo mongo:7
```
Then set `MONGODB_URI=mongodb://localhost:27017` (already the default) before
starting the backend.

## Production setup (MongoDB Atlas — free tier)

1. Create a free cluster at https://www.mongodb.com/cloud/atlas
2. Database Access → add a user with a password
3. Network Access → allow access from anywhere (`0.0.0.0/0`) for Render's
   dynamic IPs, or Render's specific egress IPs if you want it tighter
4. Get your connection string (Connect → Drivers), it looks like:
   `mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/`
5. On Render → your backend service → Environment, add:
   - `MONGODB_URI` = that connection string
   - `MONGODB_DB` = `climate_ai` (or leave unset — that's the default)
6. Redeploy. Check the Render logs for `Connected to MongoDB at ...` instead
   of the mongomock fallback warning.

## Running the injection tests

```bash
cd backend
pip install -r requirements.txt -r requirements-test.txt --break-system-packages
cd ml && python3 train.py && cd ..
pytest tests/test_security_injection.py -v
```

`tests/test_security_injection.py` runs a set of OWASP-style SQL-injection
payloads (`' OR '1'='1`, `; DROP TABLE ...`, `UNION SELECT ...`) plus MongoDB
operator-injection strings (`$ne`, `$where`, ...) against:

| Input surface | Payload delivery | Expected result |
|---|---|---|
| `/auth/login` username & password | JSON body | `400`, never `500`, never authenticates |
| `/auth/login` password as `{"$ne": null}` | JSON body (wrong type) | `422` from Pydantic type validation |
| CSV/Excel upload `district`/`state` columns | multipart file | row rejected, `rows_imported: 0` for that row |
| `mongo_service.insert_uploaded_record()` | direct call | raises `ValueError`, nothing written |

Every payload is also asserted to **never** produce a `500` — an injection
attempt should be cleanly rejected, not crash the server.

## For your STQA report

- **Test type**: this is a security/negative test suite, not just functional
  testing — it's specifically testing for *injection vulnerabilities* using
  boundary/malicious inputs rather than valid ones.
- **Why "SQL injection" tests still apply to a MongoDB app**: no SQL is ever
  executed here, so classic SQL syntax can't directly harm this system — but
  testing for it is still valuable because (a) it's a strong signal of a
  malicious/fuzzing client worth blocking outright, and (b) the equivalent,
  MongoDB-specific risk is *operator injection*, which the type-coercion
  tests (`TestMongoServiceTypeCoercion`) specifically target.
- **Results**: run `pytest tests/test_security_injection.py -v` and screenshot
  the all-green output — good evidence for "all injection payloads were
  correctly rejected without server errors."
