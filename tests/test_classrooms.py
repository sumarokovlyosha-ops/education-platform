from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def create_school(
    client: AsyncClient,
    name: str = "Test School",
) -> dict:
    response = await client.post(
        "/schools",
        json={"name": name},
    )

    assert response.status_code == 201

    return response.json()


async def create_classroom(
    client: AsyncClient,
    school_id: str,
    name: str = "10A",
    academic_year: str = "2026/2027",
) -> dict:
    response = await client.post(
        f"/schools/{school_id}/classes",
        json={
            "name": name,
            "academic_year": academic_year,
        },
    )

    assert response.status_code == 201

    return response.json()


async def test_create_classroom(
    client: AsyncClient,
) -> None:
    school = await create_school(client)

    response = await client.post(
        f"/schools/{school['id']}/classes",
        json={
            "name": "10A",
            "academic_year": "2026/2027",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["school_id"] == school["id"]
    assert data["name"] == "10A"
    assert data["academic_year"] == "2026/2027"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_get_classroom_by_id(
    client: AsyncClient,
) -> None:
    school = await create_school(client)
    classroom = await create_classroom(
        client=client,
        school_id=school["id"],
    )

    response = await client.get(
        f"/classes/{classroom['id']}",
    )

    assert response.status_code == 200
    assert response.json() == classroom


async def test_get_school_classrooms(
    client: AsyncClient,
) -> None:
    school = await create_school(client)

    first_classroom = await create_classroom(
        client=client,
        school_id=school["id"],
        name="10A",
    )
    second_classroom = await create_classroom(
        client=client,
        school_id=school["id"],
        name="10B",
    )

    response = await client.get(
        f"/schools/{school['id']}/classes",
    )

    assert response.status_code == 200

    classrooms = response.json()

    assert len(classrooms) == 2
    assert {item["id"] for item in classrooms} == {
        first_classroom["id"],
        second_classroom["id"],
    }


async def test_create_classroom_for_unknown_school_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.post(
        f"/schools/{uuid4()}/classes",
        json={
            "name": "10A",
            "academic_year": "2026/2027",
        },
    )

    assert response.status_code == 404


async def test_get_classrooms_for_unknown_school_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.get(
        f"/schools/{uuid4()}/classes",
    )

    assert response.status_code == 404


async def test_get_unknown_classroom_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.get(
        f"/classes/{uuid4()}",
    )

    assert response.status_code == 404


async def test_create_duplicate_classroom_returns_409(
    client: AsyncClient,
) -> None:
    school = await create_school(client)

    await create_classroom(
        client=client,
        school_id=school["id"],
    )

    response = await client.post(
        f"/schools/{school['id']}/classes",
        json={
            "name": "10A",
            "academic_year": "2026/2027",
        },
    )

    assert response.status_code == 409


async def test_create_classroom_with_blank_name_returns_422(
    client: AsyncClient,
) -> None:
    school = await create_school(client)

    response = await client.post(
        f"/schools/{school['id']}/classes",
        json={
            "name": "   ",
            "academic_year": "2026/2027",
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "academic_year",
    [
        "2026-2027",
        "2026/2026",
        "2026/2028",
        "abcd/efgh",
        "2026/27",
    ],
)
async def test_create_classroom_with_invalid_academic_year_returns_422(
    client: AsyncClient,
    academic_year: str,
) -> None:
    school = await create_school(client)

    response = await client.post(
        f"/schools/{school['id']}/classes",
        json={
            "name": "10A",
            "academic_year": academic_year,
        },
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "query",
    [
        "?limit=0",
        "?limit=101",
        "?offset=-1",
    ],
)
async def test_get_school_classrooms_with_invalid_pagination_returns_422(
    client: AsyncClient,
    query: str,
) -> None:
    school = await create_school(client)

    response = await client.get(
        f"/schools/{school['id']}/classes{query}",
    )

    assert response.status_code == 422


async def test_same_classroom_is_allowed_in_different_schools(
    client: AsyncClient,
) -> None:
    first_school = await create_school(client, name="First School")
    second_school = await create_school(client, name="Second School")

    first_classroom = await create_classroom(
        client=client,
        school_id=first_school["id"],
    )
    second_classroom = await create_classroom(
        client=client,
        school_id=second_school["id"],
    )

    assert first_classroom["school_id"] == first_school["id"]
    assert second_classroom["school_id"] == second_school["id"]


async def test_same_classroom_is_allowed_in_different_academic_years(
    client: AsyncClient,
) -> None:
    school = await create_school(client)

    first_classroom = await create_classroom(
        client=client,
        school_id=school["id"],
        academic_year="2026/2027",
    )
    second_classroom = await create_classroom(
        client=client,
        school_id=school["id"],
        academic_year="2027/2028",
    )

    assert first_classroom["academic_year"] == "2026/2027"
    assert second_classroom["academic_year"] == "2027/2028"


async def test_school_classroom_list_does_not_include_other_schools(
    client: AsyncClient,
) -> None:
    first_school = await create_school(client, name="First School")
    second_school = await create_school(client, name="Second School")

    first_classroom = await create_classroom(
        client=client,
        school_id=first_school["id"],
    )
    await create_classroom(
        client=client,
        school_id=second_school["id"],
    )

    response = await client.get(
        f"/schools/{first_school['id']}/classes",
    )

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [
        first_classroom["id"],
    ]
