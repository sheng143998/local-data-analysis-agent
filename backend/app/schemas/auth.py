from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


Role = Literal["analyst", "admin"]


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=12, max_length=256)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=12, max_length=256)


class UserProfile(BaseModel):
    id: UUID
    email: EmailStr
    display_name: str
    role: Role
    created_at: datetime


class AuthSessionInfo(BaseModel):
    id: UUID
    created_at: datetime
    last_seen_at: datetime
    idle_expires_at: datetime
    absolute_expires_at: datetime
    current: bool = False


class AuthResponse(BaseModel):
    user: UserProfile
    csrf_token: str


class AuthPrincipal(BaseModel):
    id: UUID
    email: str
    display_name: str
    role: Role
    session_id: UUID | None = None
    is_development_principal: bool = False
