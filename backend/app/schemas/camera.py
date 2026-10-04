from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CameraResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    camera_id: str
    tenant_id: str
    name: str
    truck_identifier: Optional[str] = None
    is_active: bool
    created_at: datetime
