import hashlib
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload
from app.modules.auth.models import User, RefreshToken

class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, user: User) -> User:
        self.db.add(user)
        await self.db.commit()
        return user

    async def get_refresh_token(self, token_hash: str) -> RefreshToken | None:
        stmt = (
            select(RefreshToken)
            .options(joinedload(RefreshToken.user))
            .where(RefreshToken.token_hash == token_hash)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.add(refresh_token)
        await self.db.commit()
        return refresh_token

    async def delete_refresh_token(self, refresh_token: RefreshToken) -> None:
        await self.db.delete(refresh_token)
        await self.db.commit()
        
    async def delete_refresh_token(self, refresh_token: RefreshToken) -> None:
        await self.db.delete(refresh_token)
        await self.db.commit()

    async def clear_expired_tokens(self) -> None:
        """It prevents the production database from becoming bloated."""
        stmt = delete(RefreshToken).where(RefreshToken.expires_at < datetime.now(timezone.utc))
        await self.db.execute(stmt)
        await self.db.commit()