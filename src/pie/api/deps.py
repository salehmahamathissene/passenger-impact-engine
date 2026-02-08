from fastapi import Depends, Header, HTTPException, Request
from jose import jwt, JWTError
from pie.core.config import settings
from pie.db.session import SessionLocal
from pie.db.models.api_key import ApiKey
from pie.core.security import api_key_hash

def db():
    s = SessionLocal()
    try:
        yield s
    finally:
        s.close()

def require_jwt(request: Request):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token")
    token = auth.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
        return payload
    except JWTError:
        raise HTTPException(401, "Invalid token")

def require_api_key(x_api_key: str = Header(default=""), session=Depends(db)):
    if not x_api_key:
        raise HTTPException(401, "Missing X-API-Key")
    h = api_key_hash(x_api_key)
    key = session.query(ApiKey).filter(ApiKey.key_hash == h, ApiKey.revoked == False).first()
    if not key:
        raise HTTPException(401, "Invalid API key")
    return key
