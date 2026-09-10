import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

pytestmark = pytest.mark.integration


async def test_register_user(
    client: AsyncClient,
    db_session: AsyncSession,
):
    response = await client.post(
        "/auth/register",
        json={
            "full_name": "Alex Test",
            "email": " Alex.Test@Example.COM ",
            "password": "password123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Alex Test"
    assert data["is_active"] is True
    assert "id" in data
    assert "email" not in data
    assert "password" not in data
    assert "password_hash" not in data

    result = await db_session.execute(
        select(User).where(User.email == "alex.test@example.com")
    )
    user = result.scalar_one()

    assert user.full_name == "Alex Test"
    assert user.email == "alex.test@example.com"
    assert user.password_hash != "password123"


async def test_register_duplicate_email_returns_409(
    client: AsyncClient,
) -> None:
    first_response = await client.post(
        "/auth/register",
        json={
            "full_name": "First User",
            "email": "duplicate@example.com",
            "password": "password123",
        },
    )

    second_response = await client.post(
        "/auth/register",
        json={
            "full_name": "Second User",
            "email": "DUPLICATE@example.com",
            "password": "password456",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"] == ("User with this email already exists")


@pytest.mark.parametrize(
    "payload",
    [
        {
            "full_name": "",
            "email": "alex@example.com",
            "password": "password123",
        },
        {
            "full_name": "A" * 256,
            "email": "alex@example.com",
            "password": "password123",
        },
        {
            "full_name": "Alex Test",
            "email": "not-an-email",
            "password": "password123",
        },
        {
            "full_name": "Alex Test",
            "email": "alex@example.com",
            "password": "1234567",
        },
        {
            "full_name": "Alex Test",
            "email": "alex@example.com",
            "password": "A" * 129,
        },
        {
            "email": "alex@example.com",
            "password": "password123",
        },
        {
            "full_name": "Alex Test",
            "password": "password123",
        },
        {
            "full_name": "Alex Test",
            "email": "alex@example.com",
        },
    ],
)
async def test_register_user_validation(
    client: AsyncClient,
    payload: dict,
):
    response = await client.post(
        "/auth/register",
        json=payload,
    )

    assert response.status_code == 422
