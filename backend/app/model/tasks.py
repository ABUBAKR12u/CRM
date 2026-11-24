from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.Base import Base, UTCDateTime, str_enum, utcnow
from app.model.users import User


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    DONE = "done"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(600), default="")
    assignee_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    creator_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    status: Mapped[TaskStatus] = mapped_column(str_enum(TaskStatus, "task_status"), default=TaskStatus.TODO)
    priority: Mapped[Priority] = mapped_column(str_enum(Priority, "task_priority"))
    due: Mapped[date]
    note: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    assignee: Mapped[User] = relationship(foreign_keys=[assignee_id], lazy="joined")
    creator: Mapped[User | None] = relationship(foreign_keys=[creator_id], lazy="joined")

    @property
    def assignee_name(self) -> str:
        return self.assignee.name

    @property
    def creator_name(self) -> str | None:
        return self.creator.name if self.creator else None
