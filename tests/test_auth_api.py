from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User


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