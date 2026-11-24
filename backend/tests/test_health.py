from httpx import AsyncClient
from sqlalchemy.exc import OperationalError

from app.database.connection import get_db
from app.main import app

BASE = "/health"


class TestLive:
    async def test_live(self, client: AsyncClient):
        resp = await client.get(BASE + "/live")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestReady:
    async def test_ready(self, client: AsyncClient):
        resp = await client.get(BASE + "/ready")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    async def test_database_down(self, client: AsyncClient):
        class BrokenSession:
            async def execute(self, *args):
                raise OperationalError("SELECT 1", {}, Exception("connection refused"))

        async def broken_db():
            yield BrokenSession()

        app.dependency_overrides[get_db] = broken_db
        resp = await client.get(BASE + "/ready")
        assert resp.status_code == 503
        assert resp.json() == {"detail": "Database unavailable"}
