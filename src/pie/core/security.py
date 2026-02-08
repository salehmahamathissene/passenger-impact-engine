import hmac, hashlib, secrets
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from pie.core.config import settings

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(p: str) -> str:
    return pwd.hash(p)

def verify_password(p: str, hashed: str) -> bool:
    return pwd.verify(p, hashed)

def create_access_token(sub: str, tenant_id: int, role: str) -> str:
    exp = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRES_MIN)
    payload = {"sub": sub, "tenant_id": tenant_id, "role": role, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)

def api_key_generate() -> str:
    return "pie_" + secrets.token_urlsafe(32)

def api_key_hash(raw: str) -> str:
    # HMAC protects against rainbow-table attacks
    mac = hmac.new(settings.API_KEY_HMAC_SECRET.encode(), raw.encode(), hashlib.sha256)
    return mac.hexdigest()
