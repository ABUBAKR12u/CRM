from datetime import UTC, datetime, timedelta

from fastapi import APIRouter
from sqlalchemy import func, select

from app.database.Base import MyDb
from app.model.tasks import TaskStatus
from app.model.users import User
from app.scheme.dashboard import StatsResponse
from app.utils.permissions import can_manage, visible_tasks
from app.utils.security import CurrentUser

router = APIRouter(tags=["Dashboard"], prefix="/dashboard")


@router.get("/stats", response_model=StatsResponse)
async def get_stats(db: MyDb, current_user: CurrentUser):
    tasks = (await db.execute(visible_tasks(current_user))).scalars().all()
    now = datetime.now(UTC)
    week_ago = now - timedelta(days=7)
    open_tasks = [task for task in tasks if task.status is not TaskStatus.DONE]
    mine = [task for task in tasks if task.assignee_id == current_user.id]

    return StatsResponse(
        users=await db.scalar(select(func.count()).select_from(User).where(User.active)),
        team_tasks=len(open_tasks),
        pending=sum(task.status is TaskStatus.REVIEW and can_manage(current_user, task) for task in tasks),
        late=sum(task.due < now.date() for task in open_tasks),
        my_tasks=sum(task.status is not TaskStatus.DONE for task in mine),
        done_week=sum(task.status is TaskStatus.DONE and task.updated_at >= week_ago for task in mine),
    )
