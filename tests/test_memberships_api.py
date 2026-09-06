from uuid import uuid4

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration


async def create_school(
    client: AsyncClient,
) -> dict:
    response = await client.post(
        "/schools",
        json={"name": "Test School"},
    )

    assert response.status_code == 201

    return response.json()


async def create_membership(
    client: AsyncClient,
    school_id: str,
    user_id: str,
) -> dict:
    response = await client.post(
        f"/schools/{school_id}/memberships",
        json={"user_id": user_id},
    )

    assert response.status_code == 201

    return response.json()


async def test_create_membership(
    client: AsyncClient,
    created_user: dict,
):
    school = await create_school(client)

    response = await client.post(
        f"/schools/{school['id']}/memberships",
        json={"user_id": created_user["id"]},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == created_user["id"]
    assert data["school_id"] == school["id"]
    assert data["is_active"] is True


async def test_create_duplicate_membership_returns_409(
    client: AsyncClient,
    created_user: dict,
):
    school = await create_school(client)

    await create_membership(
        client=client,
        school_id=school["id"],
        user_id=created_user["id"],
    )

    response = await client.post(
        f"/schools/{school['id']}/memberships",
        json={"user_id": created_user["id"]},
    )

    assert response.status_code == 409


async def test_create_membership_with_unknown_user_returns_404(
    client: AsyncClient,
):
    school = await create_school(client)

    response = await client.post(
        f"/schools/{school['id']}/memberships",
        json={"user_id": str(uuid4())},
    )

    assert response.status_code == 404


async def test_create_membership_with_unknown_school_returns_404(
    client: AsyncClient,
    created_user: dict,
):
    response = await client.post(
        f"/schools/{uuid4()}/memberships",
        json={"user_id": created_user["id"]},
    )

    assert response.status_code == 404


async def test_get_school_memberships(
    client: AsyncClient,
    created_user: dict,
):
    school = await create_school(client)

    membership = await create_membership(
        client=client,
        school_id=school["id"],
        user_id=created_user["id"],
    )

    response = await client.get(f"/schools/{school['id']}/memberships")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["id"] == membership["id"]
    assert data[0]["user_id"] == created_user["id"]


async def test_add_role_to_membership(
    client: AsyncClient,
    created_user: dict,
):
    school = await create_school(client)

    membership = await create_membership(
        client=client,
        school_id=school["id"],
        user_id=created_user["id"],
    )

    response = await client.post(
        f"/memberships/{membership['id']}/roles",
        json={"role": "teacher"},
    )

    assert response.status_code == 201

    data = response.json()

    assert data["membership_id"] == membership["id"]
    assert data["role"] == "teacher"


async def test_add_duplicate_role_returns_409(
    client: AsyncClient,
    created_user: dict,
):
    school = await create_school(client)

    membership = await create_membership(
        client=client,
        school_id=school["id"],
        user_id=created_user["id"],
    )

    await client.post(
        f"/memberships/{membership['id']}/roles",
        json={"role": "teacher"},
    )

    response = await client.post(
        f"/memberships/{membership['id']}/roles",
        json={"role": "teacher"},
    )

    assert response.status_code == 409


async def test_membership_can_have_multiple_roles(
    client: AsyncClient,
    created_user: dict,
):
    school = await create_school(client)

    membership = await create_membership(
        client=client,
        school_id=school["id"],
        user_id=created_user["id"],
    )

    first_response = await client.post(
        f"/memberships/{membership['id']}/roles",
        json={"role": "teacher"},
    )

    second_response = await client.post(
        f"/memberships/{membership['id']}/roles",
        json={"role": "schedule_manager"},
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    response = await client.get(f"/memberships/{membership['id']}/roles")

    assert response.status_code == 200

    roles = {role["role"] for role in response.json()}

    assert roles == {
        "teacher",
        "schedule_manager",
    }


async def test_remove_one_role_keeps_other_roles(
    client: AsyncClient,
    created_user: dict,
):
    school = await create_school(client)

    membership = await create_membership(
        client=client,
        school_id=school["id"],
        user_id=created_user["id"],
    )

    await client.post(
        f"/memberships/{membership['id']}/roles",
        json={"role": "teacher"},
    )

    await client.post(
        f"/memberships/{membership['id']}/roles",
        json={"role": "schedule_manager"},
    )

    delete_response = await client.delete(
        f"/memberships/{membership['id']}/roles/teacher"
    )

    assert delete_response.status_code == 204

    response = await client.get(f"/memberships/{membership['id']}/roles")

    assert response.status_code == 200

    roles = [role["role"] for role in response.json()]

    assert roles == ["schedule_manager"]


async def test_add_role_to_unknown_membership_returns_404(
    client: AsyncClient,
):
    response = await client.post(
        f"/memberships/{uuid4()}/roles",
        json={"role": "teacher"},
    )

    assert response.status_code == 404


async def test_invalid_role_returns_422(
    client: AsyncClient,
    created_user: dict,
):
    school = await create_school(client)

    membership = await create_membership(
        client=client,
        school_id=school["id"],
        user_id=created_user["id"],
    )

    response = await client.post(
        f"/memberships/{membership['id']}/roles",
        json={"role": "batman"},
    )

    assert response.status_code == 422
