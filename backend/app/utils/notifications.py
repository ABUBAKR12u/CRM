from collections.abc import Iterable
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.database.Base import MyDb
from app.model.notifications import Notification, NotificationKey
from app.model.tasks import Task, TaskStatus
from app.model.users import Role, User
from app.utils.permissions import visible_tasks


def notify(
    db: MyDb,
    actor: User | None,
    recipients: Iterable[int | None],
    key: NotificationKey,
    task: Task | None = None,
    **params: str,
) -> None:
    skip = actor.id if actor else None
    for user_id in {user_id for user_id in recipients if user_id and user_id != skip}:
        db.add(Notification(user_id=user_id, key=key, task_id=task.id if task else None, params=params))


async def admin_ids(db: MyDb) -> list[int]:
    result = await db.execute(select(User.id).where(User.role == Role.ADMIN, User.active))
    return list(result.scalars())


def task_reviewers(task: Task) -> list[int | None]:
    return [task.creator_id, task.assignee.manager_id]


async def sync_deadlines(db: MyDb, user: User) -> None:
    today = datetime.now(UTC).date()
    is_open = Task.status != TaskStatus.DONE
    checks = {
        NotificationKey.DEADLINE_SOON: select(Task).where(
            is_open, Task.assignee_id == user.id, Task.due.between(today, today + timedelta(days=1))
        ),
        NotificationKey.TASK_LATE: visible_tasks(user).where(is_open, Task.due < today, Task.assignee_id != user.id),
    }
    existing = await db.execute(
        select(Notification.task_id, Notification.key).where(
            Notification.user_id == user.id, Notification.key.in_(list(checks))
        )
    )
    seen = {(task_id, key) for task_id, key in existing}

    for key, query in checks.items():
        for task in (await db.execute(query)).scalars():
            if (task.id, key) not in seen:
                notify(db, None, [user.id], key, task, title=task.title)
    await db.commit()
