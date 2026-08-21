from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_get_user_by_id(
    client: AsyncClient,
    created_user: dict,
):
    user_id = created_user["id"]

    response = await client.get(f"/users/{user_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["full_name"] == "Created User"
    assert data["is_active"] is True


async def test_get_unknown_user_returns_404(
    client: AsyncClient,
):
    response = await client.get(
        f"/users/{uuid4()}"
    )

    assert response.status_code == 404


async def test_get_users(
    client: AsyncClient,
    created_user: dict,
):
    response = await client.get("/users")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == created_user["id"]


@pytest.mark.parametrize(
    "query",
    [
        "?limit=0",
        "?limit=101",
        "?offset=-1",
    ],
    ids=[
        "limit-too-small",
        "limit-too-large",
        "negative-offset",
    ],
)
async def test_get_users_invalid_pagination(
    client: AsyncClient,
    query: str,
):
    response = await client.get(f"/users{query}")

    assert response.status_code == 422


async def test_get_users_from_empty_database(
    client: AsyncClient,
):
    response = await client.get("/users")

    assert response.status_code == 200
    assert response.json() == []