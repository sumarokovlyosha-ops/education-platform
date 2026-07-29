from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import get_jwt_settings
from app.core.exceptions import AccessTokenError

_password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    return _password_hasher.verify(
        password,
        password_hash,
    )


def create_access_token(user_id: UUID) -> str:
    settings = get_jwt_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(
        minutes=settings.access_token_expire_minutes,
    )
    payload = {
        "sub": str(user_id),
        "iat": issued_at,
        "exp": expires_at,
    }

    return jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def decode_access_token(token: str) -> UUID:
    settings = get_jwt_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key.get_secret_value(),
            algorithms=[settings.algorithm],
            options={"require": ["sub", "exp"]},
        )
    except jwt.InvalidTokenError as error:
        raise AccessTokenError("Invalid or expired access token") from error

    subject = payload["sub"]

    if not isinstance(subject, str):
        raise AccessTokenError("Access token subject must be a string")

    try:
        return UUID(subject)
    except ValueError as error:
        raise AccessTokenError("Access token subject must be a valid UUID") from error
