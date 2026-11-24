import pytest
from pydantic import ValidationError

from app.utils.config import Environment, Settings

DB = {"DB_USERNAME": "erpcrm", "DB_PASS": "erpcrm", "DB_NAME": "erpcrm", "SECRET_KEY": "x" * 32}


class TestSettings:
    def test_production_rejects_debug(self):
        with pytest.raises(ValidationError, match="DEBUG must be false"):
            Settings(_env_file=None, ENVIRONMENT=Environment.PRODUCTION, DEBUG=True, **DB)

    def test_database_url_escapes_password(self):
        settings = Settings(_env_file=None, **{**DB, "DB_PASS": "p@ss:w/rd"})
        url = settings.DATABASE_URL
        assert url.drivername == "postgresql+asyncpg"
        assert url.password == "p@ss:w/rd"

    def test_cors_origins_from_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("CORS_ORIGINS", '["http://a.uz","http://b.uz"]')
        assert Settings(_env_file=None, **DB).CORS_ORIGINS == ["http://a.uz", "http://b.uz"]

    def test_production_requires_smtp(self):
        with pytest.raises(ValidationError, match="SMTP_HOST is required"):
            Settings(_env_file=None, ENVIRONMENT=Environment.PRODUCTION, **DB)

    def test_short_secret_rejected(self):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **{**DB, "SECRET_KEY": "short"})


class TestDocs:
    async def test_openapi(self, client):
        resp = await client.get("/openapi.json")
        assert resp.status_code == 200
        assert "/health/ready" in resp.json()["paths"]

    async def test_swagger_and_redoc(self, client):
        assert (await client.get("/docs")).status_code == 200
        assert (await client.get("/redoc")).status_code == 200
