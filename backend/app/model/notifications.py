from datetime import datetime
from enum import StrEnum

from sqlalchemy import JSON, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database.Base import Base, str_enum, utcnow


class NotificationKey(StrEnum):
    TASK_ASSIGNED = "taskAssigned"
    APPROVAL_WAITING = "approvalWaiting"
    APPROVED = "approved"
    TASK_RETURNED = "taskReturned"
    DEADLINE_SOON = "deadlineSoon"
    TASK_LATE = "taskLate"
    NEW_USER = "newUser"
    ROLE_CHANGE = "roleChange"
    PASSWORD_RESET = "passwordReset"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    key: Mapped[NotificationKey] = mapped_column(str_enum(NotificationKey, "notification_key"))
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id", ondelete="CASCADE"), index=True)
    params: Mapped[dict[str, str]] = mapped_column(JSON, default=dict)
    read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
