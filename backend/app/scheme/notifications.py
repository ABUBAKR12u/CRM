from datetime import datetime

from app.model.notifications import NotificationKey
from app.scheme.base import Schema


class NotificationResponse(Schema):
    id: int
    key: NotificationKey
    task_id: int | None
    params: dict[str, str]
    read: bool
    created_at: datetime


class NotificationList(Schema):
    items: list[NotificationResponse]
    unread: int
