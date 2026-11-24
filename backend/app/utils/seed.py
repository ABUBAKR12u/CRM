import asyncio
import sys
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from app.database.Base import Base
from app.database.connection import SessionLocal, engine
from app.model.notifications import NotificationKey
from app.model.tasks import Priority, Task, TaskStatus
from app.model.users import Role, User
from app.utils.config import Environment, settings
from app.utils.notifications import notify
from app.utils.security import hash_password

DEMO_PASSWORDS = {
    "admin@aiops.uz": "Admin#2026",
    "manager@aiops.uz": "Manager#2026",
    "employee@aiops.uz": "Employee#2026",
}

PEOPLE = [
    ("admin", "Sanjar Rasulov", "admin@aiops.uz", Role.ADMIN, "Boshqaruv", None, True),
    ("manager", "Malika Rahimova", "manager@aiops.uz", Role.MANAGER, "Moliya", None, True),
    ("employee", "Dilshod Karimov", "employee@aiops.uz", Role.EMPLOYEE, "Moliya", "manager", True),
    ("admin2", "Gulnora Ismoilova", None, Role.ADMIN, "Boshqaruv", None, True),
    ("manager2", "Javlon Ergashev", None, Role.MANAGER, "Savdo", None, True),
    ("e1", "Nodira Yusupova", None, Role.EMPLOYEE, "Moliya", "manager", True),
    ("e2", "Bobur Aliyev", None, Role.EMPLOYEE, "Moliya", "manager", True),
    ("e3", "Zilola Qodirova", None, Role.EMPLOYEE, "Moliya", "manager", True),
    ("e4", "Aziz Tursunov", None, Role.EMPLOYEE, "Savdo", "manager2", True),
    ("e5", "Madina Sodiqova", None, Role.EMPLOYEE, "Savdo", "manager2", True),
    ("e6", "Sherzod Nazarov", None, Role.EMPLOYEE, "Savdo", "manager2", True),
    ("e7", "Kamola Hasanova", None, Role.EMPLOYEE, "Marketing", None, True),
    ("e8", "Rustam Ortiqov", None, Role.EMPLOYEE, "IT", None, False),
]

S = TaskStatus
P = Priority
TASKS = [
    (
        "Oylik moliyaviy hisobotni tayyorlash",
        "Oktyabr oyi daromad va xarajatlar jadvali.",
        "employee",
        "manager",
        S.IN_PROGRESS,
        P.HIGH,
        3,
    ),
    (
        "Yetkazib beruvchilar shartnomalarini tekshirish",
        "Muddati tugayotgan 4 ta shartnoma.",
        "employee",
        "manager",
        S.TODO,
        P.MEDIUM,
        7,
    ),
    ("Byudjet rejasini yangilash", "", "employee", "manager", S.REVIEW, P.HIGH, -1),
    ("Hisob-fakturalarni solishtirish", "Bank ko'chirmasi bilan.", "e1", "manager", S.TODO, P.MEDIUM, 5),
    ("Soliq deklaratsiyasi qoralamasi", "", "e1", "manager", S.REVIEW, P.HIGH, 1),
    ("Xarajatlar kategoriyalarini tartiblash", "", "e2", "manager", S.DONE, P.LOW, -4),
    ("Debitorlik qarzlari ro'yxati", "Muddati o'tganlar birinchi.", "e2", "manager", S.IN_PROGRESS, P.HIGH, -2),
    ("Kassa hisobotini yopish", "", "e3", "manager", S.TODO, P.LOW, 9),
    ("Yangi mijozlar bazasini yuritish", "CRM'ga 30 ta yozuv.", "e4", "manager2", S.IN_PROGRESS, P.MEDIUM, 4),
    ("Savdo prognozi (Q1)", "", "e5", "manager2", S.REVIEW, P.HIGH, 2),
    ("Narxlar ro'yxatini yangilash", "", "e6", "manager2", S.TODO, P.MEDIUM, 6),
    ("Veb-sayt matnlarini tekshirish", "", "e7", "admin", S.TODO, P.LOW, 12),
    ("Xodimlar ma'lumotnomasini yangilash", "", "manager", "admin", S.IN_PROGRESS, P.MEDIUM, 5),
]

TASK_NOTIFICATION = {
    S.TODO: NotificationKey.TASK_ASSIGNED,
    S.IN_PROGRESS: NotificationKey.TASK_ASSIGNED,
    S.REVIEW: NotificationKey.APPROVAL_WAITING,
    S.DONE: NotificationKey.APPROVED,
}


def make_email(name: str) -> str:
    return ".".join("".join(ch for ch in name.lower() if ch.isalpha() or ch == " ").split()) + "@aiops.uz"


async def clear(db) -> None:
    for table in reversed(Base.metadata.sorted_tables):
        await db.execute(table.delete())
    await db.commit()


async def seed(reset: bool = False) -> None:
    if settings.ENVIRONMENT is Environment.PRODUCTION:
        raise SystemExit("Demo seed is disabled in production")

    async with SessionLocal() as db:
        if reset:
            await clear(db)
        elif await db.scalar(select(func.count()).select_from(User)):
            print("Users already exist, seed skipped")
            return

        users: dict[str, User] = {}
        for code, name, email, role, dept, _, active in PEOPLE:
            email = email or make_email(name)
            password = DEMO_PASSWORDS.get(email)
            users[code] = User(
                name=name,
                email=email,
                role=role,
                dept=dept,
                active=active,
                password_hash=hash_password(password) if password else None,
            )
        db.add_all(users.values())
        await db.flush()
        for code, *_, manager, _ in PEOPLE:
            users[code].manager_id = users[manager].id if manager else None

        today = datetime.now(UTC).date()
        for title, description, assignee, creator, status, priority, due in TASKS:
            task = Task(
                title=title,
                description=description,
                assignee_id=users[assignee].id,
                creator_id=users[creator].id,
                status=status,
                priority=priority,
                due=today + timedelta(days=due),
            )
            db.add(task)
            await db.flush()
            recipients = [users[creator].id] if status is S.REVIEW else [users[assignee].id]
            notify(db, None, recipients, TASK_NOTIFICATION[status], task, title=title, name=users[assignee].name)

        await db.commit()
        print(f"Seeded {len(PEOPLE)} users and {len(TASKS)} tasks")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed(reset="--reset" in sys.argv))
