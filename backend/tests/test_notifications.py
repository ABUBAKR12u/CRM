from datetime import date, timedelta

from httpx import AsyncClient

from app.model.tasks import TaskStatus
from app.model.users import Role
from tests.conftest import auth, make_task, make_user

BASE = "/notifications"


async def notifications(client: AsyncClient, user) -> dict:
    resp = await client.get(BASE + "/", headers=await auth(client, user))
    assert resp.status_code == 200
    return resp.json()


def keys(body: dict) -> list[str]:
    return [item["key"] for item in body["items"]]


class TestTaskEvents:
    async def test_assigned(self, client: AsyncClient, people):
        due = (date.today() + timedelta(days=5)).isoformat()
        body = {"title": "Byudjet rejasi", "assigneeId": people["employee"].id, "priority": "high", "due": due}
        await client.post("/tasks/", json=body, headers=await auth(client, people["manager"]))
        data = await notifications(client, people["employee"])
        assert keys(data) == ["taskAssigned"]
        assert data["items"][0]["params"]["title"] == "Byudjet rejasi"
        assert data["unread"] == 1

    async def test_review_notifies_creator(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["admin"], status=TaskStatus.IN_PROGRESS)
        headers = await auth(client, people["employee"])
        await client.patch(f"/tasks/{task.id}/status", json={"status": "review"}, headers=headers)
        assert "approvalWaiting" in keys(await notifications(client, people["admin"]))
        manager = await notifications(client, people["manager"])
        assert manager["items"][0]["params"]["name"] == "Dilshod Karimov"

    async def test_approved_and_returned(self, client: AsyncClient, people, db):
        approved = await make_task(db, people["employee"], people["manager"], status=TaskStatus.REVIEW)
        returned = await make_task(db, people["employee"], people["manager"], status=TaskStatus.REVIEW)
        headers = await auth(client, people["manager"])
        await client.patch(f"/tasks/{approved.id}/status", json={"status": "done"}, headers=headers)
        await client.patch(
            f"/tasks/{returned.id}/status", json={"status": "in_progress", "note": "Qayta ko'ring"}, headers=headers
        )
        data = await notifications(client, people["employee"])
        assert keys(data) == ["taskReturned", "approved"]
        assert data["items"][0]["params"]["note"] == "Qayta ko'ring"

    async def test_actor_not_notified(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"], status=TaskStatus.IN_PROGRESS)
        headers = await auth(client, people["employee"])
        await client.patch(f"/tasks/{task.id}/status", json={"status": "review"}, headers=headers)
        assert "approvalWaiting" not in keys(await notifications(client, people["employee"]))


class TestDeadlines:
    async def test_deadline_soon_created_once(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"], due_in=1)
        await make_task(db, people["employee"], people["manager"], due_in=5)
        first = await notifications(client, people["employee"])
        second = await notifications(client, people["employee"])
        assert keys(first) == ["deadlineSoon"]
        assert keys(second) == ["deadlineSoon"]

    async def test_late_for_manager_only(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"], due_in=-2)
        await make_task(db, people["employee"], people["manager"], due_in=-2, status=TaskStatus.DONE)
        assert keys(await notifications(client, people["manager"])) == ["taskLate"]
        assert keys(await notifications(client, people["employee"])) == []


class TestUserEvents:
    async def test_new_user_notifies_other_admins(self, client: AsyncClient, people, db):
        second_admin = make_user("Gulnora Ismoilova", "admin2@aiops.uz", Role.ADMIN, "Boshqaruv")
        db.add(second_admin)
        await db.commit()
        body = {"name": "Nodira Yusupova", "email": "nodira@aiops.uz", "role": "employee", "dept": "Moliya"}
        await client.post("/users/", json=body, headers=await auth(client, people["admin"]))
        data = await notifications(client, second_admin)
        assert keys(data) == ["newUser"]
        assert data["items"][0]["params"] == {"name": "Nodira Yusupova", "dept": "Moliya"}
        assert keys(await notifications(client, people["admin"])) == []

    async def test_role_change(self, client: AsyncClient, people):
        headers = await auth(client, people["admin"])
        await client.patch(f"/users/{people['employee'].id}", json={"role": "manager"}, headers=headers)
        data = await notifications(client, people["employee"])
        assert keys(data) == ["roleChange"]
        assert data["items"][0]["params"]["role"] == "manager"

    async def test_password_reset_notifies_admins(self, client: AsyncClient, people):
        resp = await client.post("/auth/forgot-password", json={"email": "employee@aiops.uz"})
        token = resp.json()["resetToken"]
        body = {"token": token, "password": "NewPass#2027", "confirm": "NewPass#2027"}
        await client.post("/auth/reset-password", json=body)
        assert keys(await notifications(client, people["admin"])) == ["passwordReset"]


class TestRead:
    async def test_read_one_and_all(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"], due_in=1)
        await make_task(db, people["employee"], people["manager"], due_in=0)
        headers = await auth(client, people["employee"])
        data = await notifications(client, people["employee"])
        assert data["unread"] == 2

        resp = await client.patch(f"{BASE}/{data['items'][0]['id']}/read", headers=headers)
        assert resp.json()["read"] is True
        assert (await notifications(client, people["employee"]))["unread"] == 1

        await client.post(BASE + "/read", headers=headers)
        assert (await notifications(client, people["employee"]))["unread"] == 0

    async def test_foreign_notification(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"], due_in=1)
        item = (await notifications(client, people["employee"]))["items"][0]
        resp = await client.patch(f"{BASE}/{item['id']}/read", headers=await auth(client, people["manager"]))
        assert resp.status_code == 404

    async def test_no_auth(self, client: AsyncClient):
        assert (await client.get(BASE + "/")).status_code == 401
