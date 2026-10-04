from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CaseBase(BaseModel):
    vin: str
    status: str = "pending_claim"


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    vin: str
    origin_tenant_id: Optional[str] = None
    origin_tenant_name: Optional[str] = None
    tenant_id: Optional[str] = None
    tenant_name: Optional[str] = None
    assigned_user_id: Optional[str] = None
    assigned_user_name: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    claimed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None


class CaseListResponse(BaseModel):
    items: List[CaseResponse]
    total: int
    page: int
    page_size: int
