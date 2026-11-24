from datetime import date, timedelta

from httpx import AsyncClient

from app.model.tasks import TaskStatus
from tests.conftest import auth, make_task

BASE = "/tasks"


def new_task(assignee_id: int, **fields) -> dict:
    due = (date.today() + timedelta(days=5)).isoformat()
    return {"title": "Byudjet rejasi", "assigneeId": assignee_id, "priority": "high", "due": due, **fields}


async def set_status(client: AsyncClient, task_id: int, headers: dict, status: str, note: str | None = None):
    return await client.patch(f"{BASE}/{task_id}/status", json={"status": status, "note": note}, headers=headers)


class TestListTasks:
    async def test_visibility_by_role(self, client: AsyncClient, people, db):
        own = await make_task(db, people["employee"], people["manager"], title="Own")
        foreign = await make_task(db, people["outsider"], people["other_manager"], title="Foreign")

        employee = await client.get(BASE + "/", headers=await auth(client, people["employee"]))
        manager = await client.get(BASE + "/", headers=await auth(client, people["manager"]))
        admin = await client.get(BASE + "/", headers=await auth(client, people["admin"]))

        assert [task["id"] for task in employee.json()] == [own.id]
        assert [task["id"] for task in manager.json()] == [own.id]
        assert {task["id"] for task in admin.json()} == {own.id, foreign.id}

    async def test_sorted_by_due(self, client: AsyncClient, people, db):
        late = await make_task(db, people["employee"], people["manager"], due_in=9)
        soon = await make_task(db, people["employee"], people["manager"], due_in=1)
        resp = await client.get(BASE + "/", headers=await auth(client, people["employee"]))
        assert [task["id"] for task in resp.json()] == [soon.id, late.id]

    async def test_response_fields(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"])
        task = (await client.get(BASE + "/", headers=await auth(client, people["employee"]))).json()[0]
        assert task["assigneeName"] == "Dilshod Karimov"
        assert task["creatorName"] == "Malika Rahimova"
        assert task["can"] == {"manage": False, "advance": ["in_progress"]}

    async def test_manager_permissions(self, client: AsyncClient, people, db):
        await make_task(db, people["employee"], people["manager"], status=TaskStatus.REVIEW)
        task = (await client.get(BASE + "/", headers=await auth(client, people["manager"]))).json()[0]
        assert task["can"] == {"manage": True, "advance": ["done", "in_progress"]}

    async def test_no_auth(self, client: AsyncClient):
        assert (await client.get(BASE + "/")).status_code == 401


class TestAssignees:
    async def test_manager_gets_team(self, client: AsyncClient, people):
        resp = await client.get(BASE + "/assignees", headers=await auth(client, people["manager"]))
        assert [user["name"] for user in resp.json()] == ["Dilshod Karimov"]

    async def test_admin_gets_non_admins(self, client: AsyncClient, people):
        resp = await client.get(BASE + "/assignees", headers=await auth(client, people["admin"]))
        assert len(resp.json()) == 4

    async def test_employee_gets_nobody(self, client: AsyncClient, people):
        resp = await client.get(BASE + "/assignees", headers=await auth(client, people["employee"]))
        assert resp.json() == []


class TestAddTask:
    async def test_manager_assigns_team(self, client: AsyncClient, people):
        headers = await auth(client, people["manager"])
        resp = await client.post(BASE + "/", json=new_task(people["employee"].id), headers=headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "todo"
        assert body["creatorId"] == people["manager"].id
        assert body["assigneeName"] == "Dilshod Karimov"

    async def test_manager_outside_team(self, client: AsyncClient, people):
        headers = await auth(client, people["manager"])
        resp = await client.post(BASE + "/", json=new_task(people["outsider"].id), headers=headers)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "invalidAssignee"

    async def test_employee_forbidden(self, client: AsyncClient, people):
        headers = await auth(client, people["employee"])
        resp = await client.post(BASE + "/", json=new_task(people["employee"].id), headers=headers)
        assert resp.status_code == 403

    async def test_validation(self, client: AsyncClient, people):
        headers = await auth(client, people["manager"])
        resp = await client.post(
            BASE + "/", json=new_task(people["employee"].id, title="ab", due="31-12-2026"), headers=headers
        )
        assert resp.status_code == 422


class TestUpdateTask:
    async def test_manager_edits(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"])
        headers = await auth(client, people["manager"])
        resp = await client.patch(
            f"{BASE}/{task.id}", json={"title": "  Yangi nom  ", "priority": "low"}, headers=headers
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Yangi nom"
        assert resp.json()["priority"] == "low"

    async def test_employee_cannot_edit(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"])
        headers = await auth(client, people["employee"])
        resp = await client.patch(f"{BASE}/{task.id}", json={"title": "Yangi nom"}, headers=headers)
        assert resp.status_code == 403

    async def test_empty_patch(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"])
        resp = await client.patch(f"{BASE}/{task.id}", json={}, headers=await auth(client, people["manager"]))
        assert resp.status_code == 400
        assert resp.json()["detail"] == "empty"

    async def test_reassign_outside_team(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"])
        headers = await auth(client, people["manager"])
        resp = await client.patch(f"{BASE}/{task.id}", json={"assigneeId": people["outsider"].id}, headers=headers)
        assert resp.status_code == 400

    async def test_hidden_task(self, client: AsyncClient, people, db):
        task = await make_task(db, people["outsider"], people["other_manager"])
        headers = await auth(client, people["manager"])
        resp = await client.patch(f"{BASE}/{task.id}", json={"title": "Yangi nom"}, headers=headers)
        assert resp.status_code == 404


class TestTaskStatus:
    async def test_employee_flow_to_review(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"])
        headers = await auth(client, people["employee"])
        assert (await set_status(client, task.id, headers, "in_progress")).status_code == 200
        resp = await set_status(client, task.id, headers, "review")
        assert resp.status_code == 200
        assert resp.json()["can"]["advance"] == []

    async def test_employee_cannot_finish(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"], status=TaskStatus.REVIEW)
        resp = await set_status(client, task.id, await auth(client, people["employee"]), "done")
        assert resp.status_code == 403

    async def test_invalid_transition(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"])
        resp = await set_status(client, task.id, await auth(client, people["employee"]), "review")
        assert resp.status_code == 409
        assert resp.json()["detail"] == "invalidTransition"

    async def test_manager_approves(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"], status=TaskStatus.REVIEW)
        resp = await set_status(client, task.id, await auth(client, people["manager"]), "done")
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

    async def test_return_requires_note(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"], status=TaskStatus.REVIEW)
        resp = await set_status(client, task.id, await auth(client, people["manager"]), "in_progress", "  ")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "noteRequired"

    async def test_return_with_note(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"], status=TaskStatus.REVIEW)
        headers = await auth(client, people["manager"])
        resp = await set_status(client, task.id, headers, "in_progress", "Jadvalni to'ldiring")
        assert resp.json()["note"] == "Jadvalni to'ldiring"
        resp = await set_status(client, task.id, await auth(client, people["employee"]), "review")
        assert resp.json()["note"] is None


class TestDeleteTask:
    async def test_manager_deletes(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"])
        resp = await client.delete(f"{BASE}/{task.id}", headers=await auth(client, people["manager"]))
        assert resp.status_code == 200
        assert resp.json()["msg"] == "Task deleted successfully"

    async def test_employee_forbidden(self, client: AsyncClient, people, db):
        task = await make_task(db, people["employee"], people["manager"])
        resp = await client.delete(f"{BASE}/{task.id}", headers=await auth(client, people["employee"]))
        assert resp.status_code == 403

    async def test_not_found(self, client: AsyncClient, people):
        resp = await client.delete(f"{BASE}/99999", headers=await auth(client, people["admin"]))
        assert resp.status_code == 404
