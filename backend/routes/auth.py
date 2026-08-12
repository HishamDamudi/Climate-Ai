import secrets
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

# Demo in-memory user store & session table.
# NOTE: replace with a hashed-password DB table + real JWT issuance for production.
_USERS = {"admin": "climate123", "viewer": "viewer123"}
_SESSIONS = {}


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(req: LoginRequest):
    if _USERS.get(req.username) != req.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = secrets.token_hex(16)
    role = "admin" if req.username == "admin" else "viewer"
    _SESSIONS[token] = {"username": req.username, "role": role}
    return {"token": token, "username": req.username, "role": role}


@router.post("/logout")
def logout(token: str):
    _SESSIONS.pop(token, None)
    return {"status": "logged_out"}


@router.get("/session")
def session(token: str):
    session = _SESSIONS.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return session
