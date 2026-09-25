from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from api.core.security import TokenManager
from api.dependencies import get_auth_service, get_token_manager
from api.schemas.auth import TokenResponse
from api.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    token_manager: TokenManager = Depends(get_token_manager)
) -> TokenResponse:
    user = auth_service.authenticate_user(
        username=form.username,
        password=form.password
    )

    if user.id is None:
        raise RuntimeError("An authenticated user must have an id")

    access_token = token_manager.create_access_token(user_id=user.id)
    return TokenResponse(access_token=access_token, token_type="Bearer")
