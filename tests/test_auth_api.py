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
            "password": "password123",
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["full_name"] == "Alex Test"
    assert data["is_active"] is True
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data

    result = await db_session.execute(
        select(User).where(User.full_name == "Alex Test")
    )
    user = result.scalar_one()

    assert user.full_name == "Alex Test"
    assert user.password_hash != "password123"



@pytest.mark.parametrize(
    "payload",
    [
        {
            "full_name": "",
            "password": "password123",
        },
        {
            "full_name": "A" * 256,
            "password": "password123",
        },
        {
            "full_name": "Alex Test",
            "password": "1234567",
        },
        {
            "full_name": "Alex Test",
            "password": "A" * 129,
        },
        {
            "password": "password123",
        },
        {
            "full_name": "Alex Test",
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