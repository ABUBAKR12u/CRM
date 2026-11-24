from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select

from app.database.Base import MyDb
from app.model.tasks import Task, TaskStatus
from app.model.users import Role, User
from app.scheme.users import TeamMemberResponse, UserResponse
from app.utils.security import require_role

router = APIRouter(tags=["Team"], prefix="/team")


@router.get("/", response_model=list[TeamMemberResponse])
async def list_team(db: MyDb, current_user: User = Depends(require_role(Role.MANAGER))):
    query = (
        select(
            User,
            func.count(case((Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]), Task.id))),
            func.count(case((Task.status == TaskStatus.REVIEW, Task.id))),
            func.count(case((Task.status == TaskStatus.DONE, Task.id))),
        )
        .outerjoin(Task, Task.assignee_id == User.id)
        .where(User.manager_id == current_user.id, User.active)
        .group_by(User.id)
        .order_by(User.name)
    )
    result = await db.execute(query)
    return [
        TeamMemberResponse(**UserResponse.model_validate(user).model_dump(), open=open_, review=review, done=done)
        for user, open_, review, done in result
    ]
