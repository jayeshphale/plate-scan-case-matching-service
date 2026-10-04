from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LoginRequest(BaseModel):
    username: str = Field(..., description="User's username or email")
    password: str = Field(..., description="User's plaintext password")


class UserAuthInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    tenant_id: str
    tenant_name: Optional[str] = None
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserAuthInfo


class TokenPayload(BaseModel):
    sub: str  # user_id
    tenant_id: str
    role: str
    exp: Optional[int] = None
