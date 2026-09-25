from api.core.config import ALGORITHM, SECRET, TOKEN_DURATION_DAYS
from api.core.exceptions import AuthenticationError
from api.core.security import PasswordHasher, TokenManager
from api.domain.user import User
from api.repositories.interfaces import UserRepository
from api.repositories.task_repository import SQLiteTaskRepository
from api.repositories.user_repository import SQLiteUserRepository
from api.services.auth_service import AuthService
from api.services.user_service import UserService
from db.session import SessionLocal
from fastapi import Depends
from api.services.task_service import TaskService
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_db():
    with SessionLocal() as session:
        yield session

def get_task_service(session = Depends(get_db)) -> TaskService:
    repository = SQLiteTaskRepository(session=session)
    return TaskService(repository)

def get_user_service(session = Depends(get_db)) -> UserService:
    repository = SQLiteUserRepository(session=session)
    password_hasher = PasswordHasher()
    return UserService(repository, password_hasher)

def get_auth_service(session = Depends(get_db)):
    repository = SQLiteUserRepository(session=session)
    password_hasher = PasswordHasher()
    return AuthService(repository, password_hasher)

def get_token_manager() -> TokenManager:
    return TokenManager(secret=SECRET, algorithm=ALGORITHM, duration_days=TOKEN_DURATION_DAYS)

def get_user_repository(session = Depends(get_db)) -> UserRepository:
    return SQLiteUserRepository(session=session)

def get_current_user(
    token:str = Depends(oauth2_scheme),
    token_manager: TokenManager = Depends(get_token_manager),
    user_repository: SQLiteUserRepository = Depends(get_user_repository)
) -> User:

    payload = token_manager.decode_access_token(token)
    subject = payload.get("sub")
    if subject is None:
        raise AuthenticationError("Invalid authentication credentials")

    try:
        user_id = int(subject)
        user = user_repository.get_by_id(user_id = user_id)
        if user is None:
            raise AuthenticationError("Invalid authentication credentials")
        return user
    except ValueError as e:
        raise AuthenticationError("Invalid authentication credentials") from e