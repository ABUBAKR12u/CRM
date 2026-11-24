from datetime import date, datetime

from pydantic import Field

from app.model.tasks import Priority, TaskStatus
from app.scheme.base import Schema


class TaskAdd(Schema):
    title: str = Field(min_length=3, max_length=120)
    description: str = Field("", max_length=600)
    assignee_id: int
    priority: Priority
    due: date


class TaskUpdate(Schema):
    title: str = Field(None, min_length=3, max_length=120)
    description: str = Field(None, max_length=600)
    assignee_id: int = None
    priority: Priority = None
    due: date = None


class TaskStatusUpdate(Schema):
    status: TaskStatus
    note: str | None = Field(None, max_length=300)


class TaskPermissions(Schema):
    manage: bool
    advance: list[TaskStatus]


class TaskOut(Schema):
    id: int
    title: str
    description: str
    assignee_id: int
    assignee_name: str
    creator_id: int | None
    creator_name: str | None
    status: TaskStatus
    priority: Priority
    due: date
    note: str | None
    updated_at: datetime


class TaskResponse(TaskOut):
    can: TaskPermissions
