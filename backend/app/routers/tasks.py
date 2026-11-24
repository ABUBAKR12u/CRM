from fastapi import APIRouter, Depends, HTTPException, status

from app.database.Base import MyDb
from app.model.notifications import NotificationKey
from app.model.tasks import Task, TaskStatus
from app.model.users import Role, User
from app.scheme.tasks import TaskAdd, TaskOut, TaskPermissions, TaskResponse, TaskStatusUpdate, TaskUpdate
from app.scheme.users import UserShort
from app.utils.checker import check_assignee, check_task
from app.utils.notifications import notify, task_reviewers
from app.utils.permissions import allowed_moves, assignable_users, can_manage, visible_tasks
from app.utils.security import CurrentUser, require_role

router = APIRouter(tags=["Tasks"], prefix="/tasks")


def task_response(user: User, task: Task) -> TaskResponse:
    can = TaskPermissions(manage=can_manage(user, task), advance=allowed_moves(user, task))
    return TaskResponse(**TaskOut.model_validate(task).model_dump(), can=can)


@router.get("/", response_model=list[TaskResponse])
async def list_tasks(db: MyDb, current_user: CurrentUser):
    result = await db.execute(visible_tasks(current_user).order_by(Task.due, Task.id))
    return [task_response(current_user, task) for task in result.scalars()]


@router.get("/assignees", response_model=list[UserShort])
async def list_assignees(db: MyDb, current_user: CurrentUser):
    result = await db.execute(assignable_users(current_user).order_by(User.name))
    return result.scalars().all()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def add_task(task: TaskAdd, db: MyDb, current_user: User = Depends(require_role(Role.ADMIN, Role.MANAGER))):
    await check_assignee(db, current_user, task.assignee_id)
    obj = Task(**task.model_dump(), creator_id=current_user.id)
    db.add(obj)
    await db.flush()
    notify(db, current_user, [obj.assignee_id], NotificationKey.TASK_ASSIGNED, obj, title=obj.title)
    await db.commit()
    await db.refresh(obj, ["assignee", "creator"])
    return task_response(current_user, obj)


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskUpdate, db: MyDb, current_user: CurrentUser):
    obj = await check_task(db, current_user, task_id)
    if not can_manage(current_user, obj):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "forbidden")
    data = task.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty")

    reassigned = data.get("assignee_id", obj.assignee_id) != obj.assignee_id
    if reassigned:
        await check_assignee(db, current_user, data["assignee_id"])

    for field, value in data.items():
        setattr(obj, field, value)
    if reassigned:
        notify(db, current_user, [obj.assignee_id], NotificationKey.TASK_ASSIGNED, obj, title=obj.title)
    await db.commit()
    await db.refresh(obj, ["assignee", "creator"])
    return task_response(current_user, obj)


@router.patch("/{task_id}/status", response_model=TaskResponse)
async def change_task_status(task_id: int, task: TaskStatusUpdate, db: MyDb, current_user: CurrentUser):
    obj = await check_task(db, current_user, task_id)
    if task.status not in allowed_moves(current_user, obj):
        if obj.assignee_id == current_user.id and task.status is TaskStatus.DONE:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "forbidden")
        raise HTTPException(status.HTTP_409_CONFLICT, "invalidTransition")

    returning = obj.status is TaskStatus.REVIEW and task.status is TaskStatus.IN_PROGRESS
    if returning and len(task.note or "") < 3:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "noteRequired")

    obj.status = task.status
    obj.note = task.note if returning else None
    if task.status is TaskStatus.REVIEW:
        notify(
            db,
            current_user,
            task_reviewers(obj),
            NotificationKey.APPROVAL_WAITING,
            obj,
            title=obj.title,
            name=obj.assignee_name,
        )
    elif task.status is TaskStatus.DONE:
        notify(db, current_user, [obj.assignee_id], NotificationKey.APPROVED, obj, title=obj.title)
    elif returning:
        notify(db, current_user, [obj.assignee_id], NotificationKey.TASK_RETURNED, obj, title=obj.title, note=obj.note)
    await db.commit()
    return task_response(current_user, obj)


@router.delete("/{task_id}")
async def delete_task(task_id: int, db: MyDb, current_user: CurrentUser):
    obj = await check_task(db, current_user, task_id)
    if not can_manage(current_user, obj):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "forbidden")
    await db.delete(obj)
    await db.commit()
    return {"msg": "Task deleted successfully"}
