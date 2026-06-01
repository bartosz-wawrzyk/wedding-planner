import logging
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.modules.auth.repository import AuthRepository
from app.modules.auth.models import User, RefreshToken
from app.modules.auth.schemas import UserRegister, UserLogin, RefreshRequest, TokenResponse
from app.core.security import (
    hash_password,
    verify_password,
    hash_token,
    create_access_token,
    generate_refresh_token,
)

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, repo: AuthRepository):
        self.repo = repo

    async def register_user(self, data: UserRegister) -> dict:
        new_user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        try:
            await self.repo.create_user(new_user)
        except IntegrityError:
            logger.warning("Registration failed: the user %s already exists", data.email)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
        return {"message": "User created"}

    async def authenticate_user(self, data: UserLogin) -> TokenResponse:
        user = await self.repo.get_user_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The account is inactive"
            )

        tokens = await self._generate_tokens_payload(user)
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            role=user.role.value
        )

    async def refresh_user_token(self, data: RefreshRequest) -> TokenResponse:
        token_hash_val = hash_token(data.refresh_token)
        db_token = await self.repo.get_refresh_token(token_hash_val)

        if not db_token:
            logger.warning("Attempt to use a non-existent or expired refresh token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        user = db_token.user

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The account is inactive"
            )

        if db_token.expires_at < datetime.now(timezone.utc):
            await self.repo.delete_refresh_token(db_token)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The token has expired"
            )

        await self.repo.delete_refresh_token(db_token)
        
        await self.repo.clear_expired_tokens()

        tokens = await self._generate_tokens_payload(user)
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            role=user.role.value
        )

    async def _generate_tokens_payload(self, user: User) -> dict:
        access_token = create_access_token(user.id)
        refresh_token_raw = generate_refresh_token()

        db_refresh = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token_raw),
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        await self.repo.create_refresh_token(db_refresh)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token_raw
        }