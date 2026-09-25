from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from api.domain.user import User
from api.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from api.services.task_service import TaskService
from api.dependencies import get_task_service, get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])

def _get_user_id(user: User) -> int:
    if user.id is None:
        raise RuntimeError("An authenticated user must have an ID.")
    return user.id

@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service)) -> TaskResponse:

    task = task_service.create_task(
        title=task_data.title,
        content=task_data.content,
        deadline=task_data.deadline,
        priority=task_data.priority,
        status=task_data.status,
        user_id=_get_user_id(current_user)
    )
    return TaskResponse.model_validate(task)

@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    tasks = task_service.list_tasks(
        user_id=_get_user_id(current_user)
    )
    return [TaskResponse.model_validate(task) for task in tasks]

@router.get("/expired", response_model=list[TaskResponse])
async def list_expired_tasks(
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> list[TaskResponse]:
    tasks = task_service.list_expired_tasks(
        user_id=_get_user_id(current_user),
        now=datetime.now(timezone.utc),
    )
    return [TaskResponse.model_validate(task) for task in tasks]

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:
    task = task_service.get_task(
        task_id=task_id,
        user_id=_get_user_id(current_user),
    )
    return TaskResponse.model_validate(task)

@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> TaskResponse:

    changes = task_data.model_dump(exclude_unset=True)
    task = task_service.update_task(
        task_id=task_id,
        user_id=_get_user_id(current_user),
        **changes,
    )
    return TaskResponse.model_validate(task)

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    task_service: TaskService = Depends(get_task_service),
) -> None:
    task_service.delete_task(
        task_id=task_id,
        user_id=_get_user_id(current_user),
    )
