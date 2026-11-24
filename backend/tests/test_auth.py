from httpx import AsyncClient

from tests.conftest import PASSWORD, auth

BASE = "/auth"


async def login(client: AsyncClient, email: str, password: str = PASSWORD):
    return await client.post(BASE + "/login", data={"username": email, "password": password})


class TestLogin:
    async def test_success(self, client: AsyncClient, people):
        resp = await login(client, "ADMIN@aiops.uz")
        assert resp.status_code == 200
        body = resp.json()
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "admin@aiops.uz"
        assert body["user"]["role"] == "admin"
        assert "managerId" in body["user"]

    async def test_wrong_password(self, client: AsyncClient, people):
        resp = await login(client, "admin@aiops.uz", "Wrong#2026")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "invalid"

    async def test_unknown_email(self, client: AsyncClient, people):
        resp = await login(client, "nobody@aiops.uz")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "invalid"

    async def test_blocked_user(self, client: AsyncClient, people, db):
        people["employee"].active = False
        await db.commit()
        resp = await login(client, "employee@aiops.uz")
        assert resp.status_code == 403
        assert resp.json()["detail"] == "blocked"

    async def test_rate_limit_after_failures(self, client: AsyncClient, people):
        for _ in range(5):
            await login(client, "admin@aiops.uz", "Wrong#2026")
        resp = await login(client, "admin@aiops.uz")
        assert resp.status_code == 429
        assert resp.json()["detail"] == "rate_limited"

    async def test_success_does_not_count(self, client: AsyncClient, people):
        for _ in range(10):
            assert (await login(client, "admin@aiops.uz")).status_code == 200


class TestMe:
    async def test_me(self, client: AsyncClient, people):
        resp = await client.get(BASE + "/me", headers=await auth(client, people["manager"]))
        assert resp.status_code == 200
        assert resp.json()["name"] == "Malika Rahimova"

    async def test_no_token(self, client: AsyncClient):
        resp = await client.get(BASE + "/me")
        assert resp.status_code == 401

    async def test_invalid_token(self, client: AsyncClient):
        resp = await client.get(BASE + "/me", headers={"Authorization": "Bearer broken"})
        assert resp.status_code == 401
        assert resp.json()["detail"] == "unauthorized"

    async def test_blocked_after_login(self, client: AsyncClient, people, db):
        headers = await auth(client, people["employee"])
        people["employee"].active = False
        await db.commit()
        resp = await client.get(BASE + "/me", headers=headers)
        assert resp.status_code == 401


class TestPasswordReset:
    async def forgot(self, client: AsyncClient, email: str) -> str | None:
        resp = await client.post(BASE + "/forgot-password", json={"email": email})
        assert resp.status_code == 200
        return resp.json().get("resetToken")

    async def test_unknown_email_same_response(self, client: AsyncClient, people):
        resp = await client.post(BASE + "/forgot-password", json={"email": "nobody@aiops.uz"})
        assert resp.status_code == 200
        assert resp.json()["resetToken"] is None

    async def test_reset_and_login(self, client: AsyncClient, people):
        token = await self.forgot(client, "employee@aiops.uz")
        new_password = "NewPass#2027"
        resp = await client.post(
            BASE + "/reset-password", json={"token": token, "password": new_password, "confirm": new_password}
        )
        assert resp.status_code == 200
        assert (await login(client, "employee@aiops.uz", new_password)).status_code == 200
        assert (await login(client, "employee@aiops.uz")).status_code == 401

    async def test_token_single_use(self, client: AsyncClient, people):
        token = await self.forgot(client, "employee@aiops.uz")
        body = {"token": token, "password": "NewPass#2027", "confirm": "NewPass#2027"}
        assert (await client.post(BASE + "/reset-password", json=body)).status_code == 200
        resp = await client.post(BASE + "/reset-password", json=body)
        assert resp.status_code == 400
        assert resp.json()["detail"] == "invalid_token"

    async def test_weak_password(self, client: AsyncClient, people):
        token = await self.forgot(client, "employee@aiops.uz")
        resp = await client.post(
            BASE + "/reset-password", json={"token": token, "password": "weakpass", "confirm": "weakpass"}
        )
        assert resp.status_code == 422

    async def test_password_mismatch(self, client: AsyncClient, people):
        token = await self.forgot(client, "employee@aiops.uz")
        resp = await client.post(
            BASE + "/reset-password", json={"token": token, "password": "NewPass#2027", "confirm": "Other#2027"}
        )
        assert resp.status_code == 422

    async def test_access_token_rejected(self, client: AsyncClient, people):
        resp = await login(client, "employee@aiops.uz")
        token = resp.json()["access_token"]
        resp = await client.post(
            BASE + "/reset-password", json={"token": token, "password": "NewPass#2027", "confirm": "NewPass#2027"}
        )
        assert resp.status_code == 400
