from fastapi import APIRouter, Depends, status
from api.schemas.user import UserCreate, UserResponse
from api.services.user_service import UserService
from api.dependencies import get_user_service, get_current_user
from api.domain.user import User

router = APIRouter(prefix="/users", tags=["Users"])

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(user_data: UserCreate, user_service: UserService = Depends(get_user_service)) -> UserResponse:
    user = user_service.register_user(
        username=user_data.username,
        email=user_data.email,
        password=user_data.password
    )
    return UserResponse.model_validate(user)

@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
)
async def read_current_user(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)
