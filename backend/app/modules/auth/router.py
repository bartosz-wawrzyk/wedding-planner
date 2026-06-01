from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.modules.auth.models import User
from app.modules.auth.repository import AuthRepository
from app.modules.auth.service import AuthService
from app.modules.auth.schemas import UserRegister, TokenResponse, UserLogin, RefreshRequest, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    repo = AuthRepository(db)
    return AuthService(repo)

async def get_current_user(
    auth: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unable to verify credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(auth.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    repo = AuthRepository(db)
    user = await repo.get_user_by_id(user_id)

    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive.",
        )
    return user

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister, service: AuthService = Depends(get_auth_service)):
    return await service.register_user(data)

@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, service: AuthService = Depends(get_auth_service)):
    return await service.authenticate_user(data)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshRequest, service: AuthService = Depends(get_auth_service)):
    return await service.refresh_user_token(data)

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user