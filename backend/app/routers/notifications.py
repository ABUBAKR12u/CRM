from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select, update

from app.database.Base import MyDb
from app.model.notifications import Notification
from app.scheme.notifications import NotificationList, NotificationResponse
from app.utils.notifications import sync_deadlines
from app.utils.security import CurrentUser

router = APIRouter(tags=["Notifications"], prefix="/notifications")

LIMIT = 30


@router.get("/", response_model=NotificationList)
async def list_notifications(db: MyDb, current_user: CurrentUser):
    await sync_deadlines(db, current_user)
    mine = Notification.user_id == current_user.id
    result = await db.execute(
        select(Notification).where(mine).order_by(Notification.created_at.desc(), Notification.id.desc()).limit(LIMIT)
    )
    unread = await db.scalar(select(func.count()).select_from(Notification).where(mine, ~Notification.read))
    return {"items": result.scalars().all(), "unread": unread}


@router.post("/read")
async def read_all_notifications(db: MyDb, current_user: CurrentUser):
    await db.execute(update(Notification).where(Notification.user_id == current_user.id).values(read=True))
    await db.commit()
    return {"msg": "Notifications marked as read"}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def read_notification(notification_id: int, db: MyDb, current_user: CurrentUser):
    obj = await db.get(Notification, notification_id)
    if not obj or obj.user_id != current_user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "notFound")
    obj.read = True
    await db.commit()
    return obj
