from datetime import timedelta

import pytest
from fakeredis import FakeAsyncRedis
from httpx import AsyncClient

from app.utils import email
from app.utils.config import settings
from app.utils.rate_limiting import RateLimiter


class FakeSMTP:
    sent: list = []

    def __init__(self, host, port, timeout):
        self.host = host

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        pass

    def login(self, username, password):
        pass

    def send_message(self, message):
        FakeSMTP.sent.append(message)


class TestRedisLimiter:
    async def test_limit_retry_and_reset(self):
        limiter = RateLimiter("test", 2, timedelta(minutes=1), FakeAsyncRedis(decode_responses=True))
        assert await limiter.retry_after("a") == 0
        await limiter.hit("a")
        await limiter.hit("a")
        assert 0 < await limiter.retry_after("a") <= 60
        assert await limiter.retry_after("b") == 0
        await limiter.reset("a")
        assert await limiter.retry_after("a") == 0


class TestLoginLimits:
    async def test_retry_after_header(self, client: AsyncClient, people):
        for _ in range(5):
            await client.post("/auth/login", data={"username": "lock@aiops.uz", "password": "Wrong#1234"})
        resp = await client.post("/auth/login", data={"username": "lock@aiops.uz", "password": "Wrong#1234"})
        assert resp.status_code == 429
        assert int(resp.headers["retry-after"]) > 0

    async def test_forwarded_ip_isolated(self, client: AsyncClient, people):
        for i in range(20):
            await client.post(
                "/auth/login",
                data={"username": f"user{i}@aiops.uz", "password": "Wrong#1234"},
                headers={"X-Forwarded-For": "10.0.0.1"},
            )
        blocked = await client.post(
            "/auth/login", data={"username": "x@aiops.uz", "password": "x"}, headers={"X-Forwarded-For": "10.0.0.1"}
        )
        other = await client.post(
            "/auth/login", data={"username": "x@aiops.uz", "password": "x"}, headers={"X-Forwarded-For": "10.0.0.2"}
        )
        assert blocked.status_code == 429
        assert other.status_code == 401


class TestResetEmail:
    async def test_email_sent_with_link(self, client: AsyncClient, people, monkeypatch: pytest.MonkeyPatch):
        FakeSMTP.sent = []
        monkeypatch.setattr(email.smtplib, "SMTP", FakeSMTP)
        monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
        resp = await client.post("/auth/forgot-password", json={"email": "employee@aiops.uz", "locale": "ru"})
        assert resp.status_code == 200
        [message] = FakeSMTP.sent
        assert message["To"] == "employee@aiops.uz"
        assert message["Subject"] == "Восстановление пароля"
        assert f"{settings.FRONTEND_URL}/ru/reset-password?token=" in message.get_content()

    async def test_no_email_for_unknown(self, client: AsyncClient, people, monkeypatch: pytest.MonkeyPatch):
        FakeSMTP.sent = []
        monkeypatch.setattr(email.smtplib, "SMTP", FakeSMTP)
        monkeypatch.setattr(settings, "SMTP_HOST", "smtp.test")
        await client.post("/auth/forgot-password", json={"email": "nobody@aiops.uz"})
        assert FakeSMTP.sent == []

    async def test_invalid_locale(self, client: AsyncClient, people):
        resp = await client.post("/auth/forgot-password", json={"email": "employee@aiops.uz", "locale": "de"})
        assert resp.status_code == 422
