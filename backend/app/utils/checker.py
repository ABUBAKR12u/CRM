from fastapi import HTTPException, status

from app.database.Base import MyDb
from app.model.tasks import Task
from app.model.users import Role, User
from app.utils.permissions import assignable_users, visible_tasks


async def check_ident(db: MyDb, model, ident: int):
    obj = await db.get(model, ident)
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "notFound")
    return obj


async def check_manager(db: MyDb, manager_id: int) -> User:
    manager = await db.get(User, manager_id)
    if not manager or manager.role is not Role.MANAGER or not manager.active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalidManager")
    return manager


async def check_assignee(db: MyDb, user: User, assignee_id: int) -> User:
    assignee = await db.scalar(assignable_users(user).where(User.id == assignee_id))
    if not assignee:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "invalidAssignee")
    return assignee


async def check_task(db: MyDb, user: User, task_id: int) -> Task:
    task = await db.scalar(visible_tasks(user).where(Task.id == task_id))
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "notFound")
    return task
