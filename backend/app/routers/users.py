from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update

from app.database.Base import MyDb
from app.model.notifications import NotificationKey
from app.model.tasks import Task, TaskStatus
from app.model.users import Role, User
from app.scheme.users import UserAdd, UserResponse, UserShort, UserUpdate
from app.utils.checker import check_ident, check_manager
from app.utils.notifications import admin_ids, notify
from app.utils.security import require_role

router = APIRouter(tags=["Users"], prefix="/users")


@router.get("/", response_model=list[UserResponse])
async def list_users(db: MyDb, current_user: User = Depends(require_role(Role.ADMIN))):
    result = await db.execute(select(User).order_by(User.name))
    return result.scalars().all()


@router.get("/managers", response_model=list[UserShort])
async def list_managers(db: MyDb, current_user: User = Depends(require_role(Role.ADMIN))):
    result = await db.execute(select(User).where(User.role == Role.MANAGER, User.active).order_by(User.name))
    return result.scalars().all()


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def add_user(user: UserAdd, db: MyDb, current_user: User = Depends(require_role(Role.ADMIN))):
    if await db.scalar(select(User.id).where(User.email == user.email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "emailTaken")

    manager_id = None
    if user.role is Role.EMPLOYEE and user.manager_id:
        manager_id = (await check_manager(db, user.manager_id)).id

    obj = User(**user.model_dump(exclude={"manager_id"}), manager_id=manager_id)
    db.add(obj)
    notify(db, current_user, await admin_ids(db), NotificationKey.NEW_USER, name=obj.name, dept=obj.dept)
    await db.commit()
    return obj


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user: UserUpdate, db: MyDb, current_user: User = Depends(require_role(Role.ADMIN))):
    obj = await check_ident(db, User, user_id)
    data = user.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "empty")

    role = data.get("role", obj.role)
    active = data.get("active", obj.active)
    if obj.id == current_user.id and (role != obj.role or not active):
        raise HTTPException(status.HTTP_409_CONFLICT, "selfAction")

    manager_id = data.pop("manager_id", obj.manager_id) if role is Role.EMPLOYEE else None
    if manager_id:
        await check_manager(db, manager_id)

    if obj.role is Role.MANAGER and role is not Role.MANAGER:
        await db.execute(update(User).where(User.manager_id == obj.id).values(manager_id=None))
    if role != obj.role:
        notify(db, current_user, [obj.id], NotificationKey.ROLE_CHANGE, role=role)

    for field, value in data.items():
        setattr(obj, field, value)
    obj.manager_id = manager_id
    await db.commit()
    return obj


@router.delete("/{user_id}")
async def delete_user(user_id: int, db: MyDb, current_user: User = Depends(require_role(Role.ADMIN))):
    obj = await check_ident(db, User, user_id)
    if obj.id == current_user.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "selfAction")

    open_task = await db.scalar(
        select(Task.id).where(Task.assignee_id == obj.id, Task.status != TaskStatus.DONE).limit(1)
    )
    if open_task:
        raise HTTPException(status.HTTP_409_CONFLICT, "hasOpenTasks")

    await db.delete(obj)
    await db.commit()
    return {"msg": "User deleted successfully"}
