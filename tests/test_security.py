from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.config import get_jwt_settings
from app.core.exceptions import AccessTokenError
from app.core.security import create_access_token, decode_access_token
from app.schemas import TokenResponse

TEST_SECRET = "test-secret-key-that-is-longer-than-32-characters"


pytestmark = pytest.mark.unit

@pytest.fixture(autouse=True)
def configure_jwt(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("JWT_SECRET_KEY", TEST_SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    get_jwt_settings.cache_clear()

    yield

    get_jwt_settings.cache_clear()


def encode_test_token(payload: dict[str, object]) -> str:
    return jwt.encode(payload, TEST_SECRET, algorithm="HS256")


def test_access_token_round_trip() -> None:
    user_id = uuid4()

    token = create_access_token(user_id)

    assert decode_access_token(token) == user_id


@pytest.mark.parametrize(
    "token",
    (
        "not-a-jwt",
        "",
    ),
)
def test_malformed_access_token_is_rejected(token: str) -> None:
    with pytest.raises(AccessTokenError):
        decode_access_token(token)


def test_expired_access_token_is_rejected() -> None:
    now = datetime.now(UTC)
    token = encode_test_token(
        {
            "sub": str(uuid4()),
            "exp": now - timedelta(seconds=1),
        }
    )

    with pytest.raises(AccessTokenError):
        decode_access_token(token)


def test_access_token_with_invalid_subject_is_rejected() -> None:
    token = encode_test_token(
        {
            "sub": "not-a-uuid",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        }
    )

    with pytest.raises(AccessTokenError):
        decode_access_token(token)


def test_access_token_without_expiration_is_rejected() -> None:
    token = encode_test_token({"sub": str(uuid4())})

    with pytest.raises(AccessTokenError):
        decode_access_token(token)


def test_token_response_uses_bearer_by_default() -> None:
    response = TokenResponse(access_token="encoded-token")

    assert response.token_type == "bearer"
