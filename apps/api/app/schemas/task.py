from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.task import TaskStatus


class TaskBase(BaseModel):
    title: str
    description: str | None = None
    due_date: date | None = None
    client_id: int | None = None


class TaskCreate(TaskBase):
    """Payload for POST /tasks. advisor_id is taken from the
    authenticated advisor, never from the request body. If client_id
    is set, it must belong to a client owned by that same advisor."""


class TaskUpdate(BaseModel):
    """Payload for PATCH /tasks/{task_id}. All fields optional so the
    advisor can update just what changed."""

    title: str | None = None
    description: str | None = None
    due_date: date | None = None
    client_id: int | None = None
    status: TaskStatus | None = None


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    advisor_id: int
    status: TaskStatus
    created_at: datetime
    completed_at: datetime | None
