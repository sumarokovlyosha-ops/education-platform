from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def test_create_school(
    client: AsyncClient,
):
    response = await client.post(
        "/schools",
        json={"name": "Test School"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test School"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_get_school_by_id(
    client: AsyncClient,
):
    create_response = await client.post(
        "/schools",
        json={"name": "Test School"},
    )

    school_id = create_response.json()["id"]

    response = await client.get(
        f"/schools/{school_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == school_id
    assert data["name"] == "Test School"
    assert data["is_active"] is True


async def test_get_unknown_school_returns_404(
    client: AsyncClient,
):
    response = await client.get(
        f"/schools/{uuid4()}"
    )

    assert response.status_code == 404


async def test_get_schools(
    client: AsyncClient,
):
    await client.post(
        "/schools",
        json={"name": "First School"},
    )

    await client.post(
        "/schools",
        json={"name": "Second School"},
    )

    response = await client.get("/schools")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) == 2


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
async def test_get_schools_invalid_pagination(
    client: AsyncClient,
    query: str,
):
    response = await client.get(
        f"/schools{query}"
    )

    assert response.status_code == 422


async def test_create_school_with_blank_name_returns_422(
    client: AsyncClient,
):
    response = await client.post(
        "/schools",
        json={"name": "   "},
    )

    assert response.status_code == 422