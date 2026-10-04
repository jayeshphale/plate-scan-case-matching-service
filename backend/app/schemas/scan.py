from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ScanCreate(BaseModel):
    camera_id: str = Field(..., description="External camera identifier, e.g. cam_1001")
    plate: str = Field(..., description="License plate string")
    vin: str = Field(..., description="Vehicle Identification Number")
    latitude: float = Field(..., description="GPS latitude")
    longitude: float = Field(..., description="GPS longitude")
    scanned_at: datetime = Field(..., description="Timestamp when scan was captured")
    image_url: Optional[str] = Field(None, description="URL pointing to plate/vehicle image")


class ScanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    camera_id: str
    plate: str
    vin: str
    latitude: float
    longitude: float
    scanned_at: datetime
    image_url: Optional[str] = None
    created_at: datetime


class ScanIngestResponse(BaseModel):
    scan_id: str
    tenant_id: str
    vin: str
    matched_existing_case: bool
    created_new_case: bool
    case_id: Optional[str] = None
    case_status: Optional[str] = None
    message: str
