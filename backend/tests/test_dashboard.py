from httpx import AsyncClient

from app.model.tasks import TaskStatus
from tests.conftest import auth, make_task


class TestTeam:
    async def test_counts(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"])
        await make_task(db, people["employee"], people["manager"], status=TaskStatus.IN_PROGRESS)
        await make_task(db, people["employee"], people["manager"], status=TaskStatus.REVIEW)
        await make_task(db, people["employee"], people["manager"], status=TaskStatus.DONE)
        resp = await client.get("/team/", headers=await auth(client, people["manager"]))
        assert resp.status_code == 200
        [member] = resp.json()
        assert member["name"] == "Dilshod Karimov"
        assert (member["open"], member["review"], member["done"]) == (2, 1, 1)

    async def test_member_without_tasks(self, client: AsyncClient, people):
        resp = await client.get("/team/", headers=await auth(client, people["manager"]))
        assert resp.json()[0]["open"] == 0

    async def test_employee_forbidden(self, client: AsyncClient, people):
        resp = await client.get("/team/", headers=await auth(client, people["employee"]))
        assert resp.status_code == 403


class TestStats:
    async def test_manager_stats(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"], status=TaskStatus.REVIEW)
        await make_task(db, people["employee"], people["manager"], due_in=-2)
        await make_task(db, people["manager"], people["admin"], status=TaskStatus.DONE)
        resp = await client.get("/dashboard/stats", headers=await auth(client, people["manager"]))
        assert resp.json() == {"users": 5, "teamTasks": 2, "pending": 1, "late": 1, "myTasks": 0, "doneWeek": 1}

    async def test_employee_stats(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"])
        await make_task(db, people["outsider"], people["other_manager"])
        resp = await client.get("/dashboard/stats", headers=await auth(client, people["employee"]))
        body = resp.json()
        assert (body["teamTasks"], body["myTasks"], body["pending"]) == (1, 1, 0)
