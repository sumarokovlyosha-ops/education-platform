from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from app.core.config import get_jwt_settings
from app.core.exceptions import AccessTokenError
from app.core.security import create_access_token, decode_access_token


def assert_token_rejected(token: str, scenario: str) -> None:
    try:
        decode_access_token(token)
    except AccessTokenError:
        print(f"[OK] {scenario}")
    else:
        raise AssertionError(f"Token was accepted: {scenario}")


def encode_test_token(payload: dict[str, object]) -> str:
    settings = get_jwt_settings()

    return jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def main() -> None:
    original_user_id = uuid4()
    token = create_access_token(original_user_id)
    decoded_user_id = decode_access_token(token)

    assert isinstance(token, str)
    assert isinstance(decoded_user_id, UUID)
    assert decoded_user_id == original_user_id
    print("[OK] UUID round trip")

    assert_token_rejected(
        "this-is-not-a-jwt",
        "malformed token rejected",
    )

    header, payload, signature = token.split(".")
    replacement = "A" if signature[0] != "A" else "B"
    modified_token = ".".join(
        (
            header,
            payload,
            replacement + signature[1:],
        )
    )
    assert_token_rejected(
        modified_token,
        "modified signature rejected",
    )

    now = datetime.now(UTC)
    invalid_subject_token = encode_test_token(
        {
            "sub": "not-a-uuid",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
    )
    assert_token_rejected(
        invalid_subject_token,
        "invalid subject rejected",
    )

    expired_token = encode_test_token(
        {
            "sub": str(uuid4()),
            "iat": now - timedelta(minutes=2),
            "exp": now - timedelta(minutes=1),
        }
    )
    assert_token_rejected(
        expired_token,
        "expired token rejected",
    )

    token_without_expiration = encode_test_token(
        {
            "sub": str(uuid4()),
            "iat": now,
        }
    )
    assert_token_rejected(
        token_without_expiration,
        "token without expiration rejected",
    )

    print("JWT smoke check passed")


if __name__ == "__main__":
    main()
