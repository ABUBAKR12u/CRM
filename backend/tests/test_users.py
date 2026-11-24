from httpx import AsyncClient
from sqlalchemy import select

from app.model.tasks import Task, TaskStatus
from tests.conftest import auth, make_task

BASE = "/users"


def new_user(**fields) -> dict:
    return {"name": "Nodira Yusupova", "email": "Nodira@AIops.uz", "role": "employee", "dept": "Moliya", **fields}


class TestListUsers:
    async def test_admin_lists_sorted(self, client: AsyncClient, people):
        resp = await client.get(BASE + "/", headers=await auth(client, people["admin"]))
        assert resp.status_code == 200
        names = [user["name"] for user in resp.json()]
        assert names == sorted(names)
        assert len(names) == 5

    async def test_manager_forbidden(self, client: AsyncClient, people):
        resp = await client.get(BASE + "/", headers=await auth(client, people["manager"]))
        assert resp.status_code == 403
        assert resp.json()["detail"] == "forbidden"

    async def test_managers_list(self, client: AsyncClient, people):
        resp = await client.get(BASE + "/managers", headers=await auth(client, people["admin"]))
        assert {user["name"] for user in resp.json()} == {"Malika Rahimova", "Javlon Ergashev"}


class TestAddUser:
    async def test_create_with_manager(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.post(BASE + "/", json=new_user(managerId=people["manager"].id), headers=headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["email"] == "nodira@aiops.uz"
        assert body["managerId"] == people["manager"].id
        assert body["active"] is True

    async def test_manager_ignored_for_non_employee(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.post(
            BASE + "/", json=new_user(role="manager", managerId=people["manager"].id), headers=headers
        )
        assert resp.status_code == 201
        assert resp.json()["managerId"] is None

    async def test_email_taken(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.post(BASE + "/", json=new_user(email="EMPLOYEE@aiops.uz"), headers=headers)
        assert resp.status_code == 409
        assert resp.json()["detail"] == "emailTaken"

    async def test_invalid_manager(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.post(BASE + "/", json=new_user(managerId=people["employee"].id), headers=headers)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "invalidManager"

    async def test_validation(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.post(BASE + "/", json=new_user(name="A", email="not-email"), headers=headers)
        assert resp.status_code == 422


class TestUpdateUser:
    async def test_update_fields(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.patch(f"{BASE}/{people['employee'].id}", json={"dept": "IT"}, headers=headers)
        assert resp.status_code == 200
        assert resp.json()["dept"] == "IT"
        assert resp.json()["managerId"] == people["manager"].id

    async def test_empty_patch(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.patch(f"{BASE}/{people['employee'].id}", json={}, headers=headers)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "empty"

    async def test_self_demote(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.patch(f"{BASE}/{people['admin'].id}", json={"role": "manager"}, headers=headers)
        assert resp.status_code == 409
        assert resp.json()["detail"] == "selfAction"

    async def test_self_deactivate(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.patch(f"{BASE}/{people['admin'].id}", json={"active": False}, headers=headers)
        assert resp.status_code == 409

    async def test_manager_demoted_frees_team(self, client: AsyncClient, people, db):
        headers = await auth(client, people["admin"])
        resp = await client.patch(f"{BASE}/{people['manager'].id}", json={"role": "employee"}, headers=headers)
        assert resp.status_code == 200
        await db.refresh(people["employee"])
        assert people["employee"].manager_id is None

    async def test_role_change_clears_manager(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.patch(f"{BASE}/{people['employee'].id}", json={"role": "manager"}, headers=headers)
        assert resp.json()["managerId"] is None

    async def test_null_name_rejected(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.patch(f"{BASE}/{people['employee'].id}", json={"name": None}, headers=headers)
        assert resp.status_code == 422

    async def test_not_found(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.patch(f"{BASE}/99999", json={"dept": "IT"}, headers=headers)
        assert resp.status_code == 404
        assert resp.json()["detail"] == "notFound"


class TestDeleteUser:
    async def test_delete_removes_done_tasks(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"], status=TaskStatus.DONE)
        headers = await auth(client, people["admin"])
        resp = await client.delete(f"{BASE}/{people['employee'].id}", headers=headers)
        assert resp.status_code == 200
        assert await db.scalar(select(Task.id)) is None

    async def test_has_open_tasks(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"])
        headers = await auth(client, people["admin"])
        resp = await client.delete(f"{BASE}/{people['employee'].id}", headers=headers)
        assert resp.status_code == 409
        assert resp.json()["detail"] == "hasOpenTasks"

    async def test_delete_manager_frees_team(self, client: AsyncClient, people, db):
        headers = await auth(client, people["admin"])
        assert (await client.delete(f"{BASE}/{people['manager'].id}", headers=headers)).status_code == 200
        await db.refresh(people["employee"])
        assert people["employee"].manager_id is None

    async def test_delete_self(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        resp = await client.delete(f"{BASE}/{people['admin'].id}", headers=headers)
        assert resp.status_code == 409
        assert resp.json()["detail"] == "selfAction"
