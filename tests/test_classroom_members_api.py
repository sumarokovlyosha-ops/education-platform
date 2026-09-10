from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.classroom import Classroom
from app.models.membership import Membership

pytestmark = pytest.mark.integration


async def create_user(
    client: AsyncClient,
    full_name: str,
    email: str,
) -> dict:
    response = await client.post(
        "/auth/register",
        json={
            "full_name": full_name,
            "email": email,
            "password": "password123",
        },
    )

    assert response.status_code == 201
    return response.json()


async def create_school(
    client: AsyncClient,
    name: str,
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
) -> dict:
    response = await client.post(
        f"/schools/{school_id}/classes",
        json={
            "name": name,
            "academic_year": "2026/2027",
        },
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


async def add_membership_role(
    client: AsyncClient,
    membership_id: str,
    role: str,
) -> None:
    response = await client.post(
        f"/memberships/{membership_id}/roles",
        json={"role": role},
    )

    assert response.status_code == 201


@pytest.mark.parametrize("role", ["student", "teacher"])
async def test_add_classroom_member(
    client: AsyncClient,
    created_user: dict,
    role: str,
) -> None:
    school = await create_school(client, name="Member School")
    classroom = await create_classroom(client, school_id=school["id"])
    membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=created_user["id"],
    )
    await add_membership_role(client, membership["id"], role=role)

    response = await client.post(
        f"/classes/{classroom['id']}/members",
        json={
            "membership_id": membership["id"],
            "role": role,
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["classroom_id"] == classroom["id"]
    assert data["membership_id"] == membership["id"]
    assert data["role"] == role
    assert "joined_at" in data


async def test_add_duplicate_classroom_member_returns_409(
    client: AsyncClient,
    created_user: dict,
) -> None:
    school = await create_school(client, name="Duplicate Member School")
    classroom = await create_classroom(client, school_id=school["id"])
    membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=created_user["id"],
    )
    await add_membership_role(client, membership["id"], role="student")

    payload = {
        "membership_id": membership["id"],
        "role": "student",
    }

    first_response = await client.post(
        f"/classes/{classroom['id']}/members",
        json=payload,
    )
    second_response = await client.post(
        f"/classes/{classroom['id']}/members",
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409


async def test_add_member_from_another_school_returns_409(
    client: AsyncClient,
    created_user: dict,
) -> None:
    classroom_school = await create_school(client, name="Classroom School")
    membership_school = await create_school(client, name="Membership School")
    classroom = await create_classroom(client, school_id=classroom_school["id"])
    membership = await create_membership(
        client,
        school_id=membership_school["id"],
        user_id=created_user["id"],
    )
    await add_membership_role(client, membership["id"], role="student")

    response = await client.post(
        f"/classes/{classroom['id']}/members",
        json={
            "membership_id": membership["id"],
            "role": "student",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Classroom and membership belong to different schools"
    )


async def test_add_member_without_required_role_returns_409(
    client: AsyncClient,
    created_user: dict,
) -> None:
    school = await create_school(client, name="Role School")
    classroom = await create_classroom(client, school_id=school["id"])
    membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=created_user["id"],
    )
    await add_membership_role(client, membership["id"], role="student")

    response = await client.post(
        f"/classes/{classroom['id']}/members",
        json={
            "membership_id": membership["id"],
            "role": "teacher",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Membership does not have the required school role"
    )


async def test_add_member_to_unknown_classroom_returns_404(
    client: AsyncClient,
    created_user: dict,
) -> None:
    school = await create_school(client, name="Unknown Classroom School")
    membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=created_user["id"],
    )
    await add_membership_role(client, membership["id"], role="student")

    response = await client.post(
        f"/classes/{uuid4()}/members",
        json={
            "membership_id": membership["id"],
            "role": "student",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Classroom not found"


async def test_add_unknown_membership_returns_404(
    client: AsyncClient,
) -> None:
    school = await create_school(client, name="Unknown Membership School")
    classroom = await create_classroom(client, school_id=school["id"])

    response = await client.post(
        f"/classes/{classroom['id']}/members",
        json={
            "membership_id": str(uuid4()),
            "role": "student",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Membership not found"


async def test_add_member_to_inactive_classroom_returns_409(
    client: AsyncClient,
    db_session: AsyncSession,
    created_user: dict,
) -> None:
    school = await create_school(client, name="Inactive Classroom School")
    classroom = await create_classroom(client, school_id=school["id"])
    membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=created_user["id"],
    )
    await add_membership_role(client, membership["id"], role="student")

    orm_classroom = await db_session.get(Classroom, UUID(classroom["id"]))
    assert orm_classroom is not None
    orm_classroom.is_active = False
    await db_session.flush()

    response = await client.post(
        f"/classes/{classroom['id']}/members",
        json={
            "membership_id": membership["id"],
            "role": "student",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Classroom is inactive"


async def test_add_inactive_membership_returns_409(
    client: AsyncClient,
    db_session: AsyncSession,
    created_user: dict,
) -> None:
    school = await create_school(client, name="Inactive Membership School")
    classroom = await create_classroom(client, school_id=school["id"])
    membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=created_user["id"],
    )
    await add_membership_role(client, membership["id"], role="student")

    orm_membership = await db_session.get(Membership, UUID(membership["id"]))
    assert orm_membership is not None
    orm_membership.is_active = False
    await db_session.flush()

    response = await client.post(
        f"/classes/{classroom['id']}/members",
        json={
            "membership_id": membership["id"],
            "role": "student",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Membership is inactive"


async def test_list_classroom_members(
    client: AsyncClient,
    created_user: dict,
) -> None:
    second_user = await create_user(
        client,
        full_name="Second Member",
        email="second.member@example.com",
    )
    school = await create_school(client, name="Member List School")
    classroom = await create_classroom(client, school_id=school["id"])

    first_membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=created_user["id"],
    )
    second_membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=second_user["id"],
    )

    for membership in (first_membership, second_membership):
        await add_membership_role(client, membership["id"], role="student")

        response = await client.post(
            f"/classes/{classroom['id']}/members",
            json={
                "membership_id": membership["id"],
                "role": "student",
            },
        )

        assert response.status_code == 201

    response = await client.get(
        f"/classes/{classroom['id']}/members",
    )

    assert response.status_code == 200
    assert {item["membership_id"] for item in response.json()} == {
        first_membership["id"],
        second_membership["id"],
    }


async def test_list_members_of_unknown_classroom_returns_404(
    client: AsyncClient,
) -> None:
    response = await client.get(
        f"/classes/{uuid4()}/members",
    )

    assert response.status_code == 404


@pytest.mark.parametrize(
    "query",
    [
        "?limit=0",
        "?limit=101",
        "?offset=-1",
    ],
)
async def test_list_members_with_invalid_pagination_returns_422(
    client: AsyncClient,
    query: str,
) -> None:
    response = await client.get(
        f"/classes/{uuid4()}/members{query}",
    )

    assert response.status_code == 422


async def test_remove_classroom_member(
    client: AsyncClient,
    created_user: dict,
) -> None:
    school = await create_school(client, name="Remove Member School")
    classroom = await create_classroom(client, school_id=school["id"])
    membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=created_user["id"],
    )
    await add_membership_role(client, membership["id"], role="student")

    await client.post(
        f"/classes/{classroom['id']}/members",
        json={
            "membership_id": membership["id"],
            "role": "student",
        },
    )

    delete_response = await client.delete(
        f"/classes/{classroom['id']}/members/{membership['id']}",
    )

    assert delete_response.status_code == 204

    list_response = await client.get(
        f"/classes/{classroom['id']}/members",
    )

    assert list_response.status_code == 200
    assert list_response.json() == []

    second_delete_response = await client.delete(
        f"/classes/{classroom['id']}/members/{membership['id']}",
    )

    assert second_delete_response.status_code == 404


async def test_cannot_remove_membership_role_used_in_classroom(
    client: AsyncClient,
    created_user: dict,
) -> None:
    school = await create_school(client, name="Used Role School")
    classroom = await create_classroom(client, school_id=school["id"])
    membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=created_user["id"],
    )
    await add_membership_role(client, membership["id"], role="student")

    await client.post(
        f"/classes/{classroom['id']}/members",
        json={
            "membership_id": membership["id"],
            "role": "student",
        },
    )

    response = await client.delete(
        f"/memberships/{membership['id']}/roles/student",
    )

    assert response.status_code == 409
    assert response.json()["detail"] == ("Role is used by a classroom membership")


async def test_invalid_classroom_role_returns_422(
    client: AsyncClient,
    created_user: dict,
) -> None:
    school = await create_school(client, name="Invalid Role School")
    classroom = await create_classroom(client, school_id=school["id"])
    membership = await create_membership(
        client,
        school_id=school["id"],
        user_id=created_user["id"],
    )

    response = await client.post(
        f"/classes/{classroom['id']}/members",
        json={
            "membership_id": membership["id"],
            "role": "admin",
        },
    )

    assert response.status_code == 422
