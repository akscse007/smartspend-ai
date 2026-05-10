import hashlib
import hmac
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

try:
    import jwt
    from jwt import InvalidTokenError
except ImportError:  # pragma: no cover - handled at runtime
    jwt = None  # type: ignore[assignment]
    InvalidTokenError = Exception  # type: ignore[assignment]

from app.config import settings


bearer_scheme = HTTPBearer(auto_error=False)
JWT_MISSING_MESSAGE = (
    "PyJWT is not installed in the Python environment running the backend. "
    "Activate backend/.venv or run `pip install -r backend/requirements.txt`."
)


@dataclass
class AuthUser:
    user_id: int
    email: str | None = None
    full_name: str | None = None


def ensure_jwt_dependency() -> None:
    if jwt is None:
        raise RuntimeError(JWT_MISSING_MESSAGE)


def _get_jwt_module():
    if jwt is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=JWT_MISSING_MESSAGE,
        )
    return jwt


def hash_password(password: str, salt: str | None = None) -> str:
    actual_salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), actual_salt.encode("utf-8"), 120_000).hex()
    return f"{actual_salt}${digest}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        salt, stored_hash = encoded.split("$", 1)
    except ValueError:
        return False
    computed = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(computed, stored_hash)


def create_access_token(user_id: int, email: str, full_name: str) -> str:
    jwt_module = _get_jwt_module()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "user_id": user_id,
        "email": email,
        "full_name": full_name,
        "exp": expires_at,
    }
    return jwt_module.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def _decode_user(credentials: HTTPAuthorizationCredentials | None) -> AuthUser | None:
    if credentials is None:
        return None
    jwt_module = _get_jwt_module()
    try:
        payload = jwt_module.decode(credentials.credentials, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    token_user = payload.get("sub") or payload.get("user_id")
    if token_user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing user id")

    try:
        return AuthUser(
            user_id=int(token_user),
            email=payload.get("email"),
            full_name=payload.get("full_name"),
        )
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user id in token") from exc


def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> AuthUser:
    decoded = _decode_user(credentials)
    if decoded is not None:
        return decoded

    if settings.auth_required:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    return AuthUser(user_id=settings.default_user_id, email="guest@local", full_name="Guest User")
