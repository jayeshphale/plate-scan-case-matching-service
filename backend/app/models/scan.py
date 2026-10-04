import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Index
from app.db.database import Base


class Scan(Base):
    __tablename__ = "scans"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    camera_id = Column(String(100), nullable=False, index=True)
    plate = Column(String(20), nullable=False, index=True)
    vin = Column(String(50), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    scanned_at = Column(DateTime, nullable=False, index=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("ix_scans_vin_scanned_at", "vin", "scanned_at"),
    )
