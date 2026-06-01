from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from uuid import UUID

class UserBase(BaseModel):
    email: EmailStr

    @field_validator("email", mode="after")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()

class UserRegister(UserBase):
    password: str

class UserLogin(UserBase):
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str

class RefreshRequest(BaseModel):
    refresh_token: str

class UserRead(UserBase):
    id: UUID
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)