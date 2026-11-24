import asyncio
from datetime import date, timedelta

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.database.Base import Base
from app.database.connection import create_database, get_db
from app.main import app
from app.model.tasks import Priority, Task, TaskStatus
from app.model.users import Role, User
from app.utils.config import settings
from app.utils.rate_limiting import LIMITERS
from app.utils.security import hash_password

TEST_DB_URL = settings.DATABASE_URL.set(database=f"{settings.DB_NAME}_test")
PASSWORD = "Secret#2026"
PASSWORD_HASH = hash_password(PASSWORD)


@pytest.fixture(autouse=True)
def clear_rate_limits():
    for limiter in LIMITERS:
        limiter.buckets.clear()


async def rebuild_schema(create: bool):
    await create_database(TEST_DB_URL)
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        if create:
            await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()


@pytest.fixture(scope="session")
def db_schema():
    asyncio.run(rebuild_schema(create=True))
    yield
    asyncio.run(rebuild_schema(create=False))


@pytest_asyncio.fixture(scope="function")
async def db_engine(db_schema):
    engine = create_async_engine(TEST_DB_URL, poolclass=NullPool)
    yield engine
    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session_maker(db_engine):
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db(session_maker):
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(session_maker):
    async def override_get_db():
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def people(db):
    admin = make_user("Sanjar Rasulov", "admin@aiops.uz", Role.ADMIN, "Boshqaruv")
    manager = make_user("Malika Rahimova", "manager@aiops.uz", Role.MANAGER, "Moliya")
    other_manager = make_user("Javlon Ergashev", "manager2@aiops.uz", Role.MANAGER, "Savdo")
    db.add_all([admin, manager, other_manager])
    await db.flush()
    employee = make_user("Dilshod Karimov", "employee@aiops.uz", Role.EMPLOYEE, "Moliya", manager.id)
    outsider = make_user("Aziz Tursunov", "outsider@aiops.uz", Role.EMPLOYEE, "Savdo", other_manager.id)
    db.add_all([employee, outsider])
    await db.commit()
    return {
        "admin": admin,
        "manager": manager,
        "other_manager": other_manager,
        "employee": employee,
        "outsider": outsider,
    }


def make_user(name, email, role, dept, manager_id=None, active=True):
    return User(
        name=name,
        email=email,
        role=role,
        dept=dept,
        manager_id=manager_id,
        active=active,
        password_hash=PASSWORD_HASH,
    )


async def make_task(db, assignee, creator, status=TaskStatus.TODO, due_in=3, title="Oylik hisobot"):
    task = Task(
        title=title,
        assignee_id=assignee.id,
        creator_id=creator.id,
        status=status,
        priority=Priority.MEDIUM,
        due=date.today() + timedelta(days=due_in),
    )
    db.add(task)
    await db.commit()
    return task


async def auth(client: AsyncClient, user: User) -> dict:
    resp = await client.post("/auth/login", data={"username": user.email, "password": PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
