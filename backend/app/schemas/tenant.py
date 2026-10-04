from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TenantBase(BaseModel):
    name: str


class TenantResponse(TenantBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
