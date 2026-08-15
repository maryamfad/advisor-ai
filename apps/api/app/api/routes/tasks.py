from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import (
    get_current_advisor_id,
    get_db,
    get_owned_client,
    get_owned_task,
)
from app.models.client import Client
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Read-only convenience route for browsing one client's tasks. Separate
# router (different prefix) registered alongside the one above.
client_tasks_router = APIRouter(prefix="/clients/{client_id}/tasks", tags=["tasks"])


def _validate_client_ownership(
    db: Session, client_id: int | None, advisor_id: int
) -> None:
    """If a client_id is supplied, make sure it refers to a client
    actually owned by the acting advisor -- otherwise an advisor could
    link a task to a client that isn't theirs."""
    if client_id is None:
        return

    client = db.get(Client, client_id)

    if client is None or client.advisor_id != advisor_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No client with id {client_id} owned by this advisor.",
        )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
) -> Task:
    _validate_client_ownership(db, payload.client_id, advisor_id)

    task = Task(
        advisor_id=advisor_id,
        client_id=payload.client_id,
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(
    db: Session = Depends(get_db),
    advisor_id: int = Depends(get_current_advisor_id),
    client_id: int | None = None,
    status_filter: TaskStatus | None = None,
) -> list[Task]:
    stmt = select(Task).where(Task.advisor_id == advisor_id)

    if client_id is not None:
        stmt = stmt.where(Task.client_id == client_id)

    if status_filter is not None:
        stmt = stmt.where(Task.status == status_filter)

    return list(db.scalars(stmt).all())


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task: Task = Depends(get_owned_task)) -> Task:
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    task: Task = Depends(get_owned_task),
    advisor_id: int = Depends(get_current_advisor_id),
) -> Task:
    updates = payload.model_dump(exclude_unset=True)

    if "client_id" in updates:
        _validate_client_ownership(db, updates["client_id"], advisor_id)

    was_completed = task.status == TaskStatus.COMPLETED

    for field, value in updates.items():
        setattr(task, field, value)

    # Deterministic bookkeeping, not left to the caller: completing a
    # task stamps completed_at; moving it off "completed" clears it.
    is_now_completed = task.status == TaskStatus.COMPLETED
    if is_now_completed and not was_completed:
        task.completed_at = datetime.utcnow()
    elif not is_now_completed and was_completed:
        task.completed_at = None

    db.commit()
    db.refresh(task)

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    db: Session = Depends(get_db),
    task: Task = Depends(get_owned_task),
) -> None:
    db.delete(task)
    db.commit()


@client_tasks_router.get("", response_model=list[TaskRead])
def list_client_tasks(
    db: Session = Depends(get_db),
    client: Client = Depends(get_owned_client),
) -> list[Task]:
    stmt = select(Task).where(Task.client_id == client.id)

    return list(db.scalars(stmt).all())
