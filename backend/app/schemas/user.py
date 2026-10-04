from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    role: str = "staff"
    is_active: bool = True


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    tenant_id: str
    tenant_name: Optional[str] = None
    created_at: datetime
