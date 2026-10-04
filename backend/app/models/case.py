import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, text
from sqlalchemy.orm import relationship
from app.db.database import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vin = Column(String(50), nullable=False, index=True)
    
    # origin_tenant_id records which tenant's camera sighted the vehicle to trigger case creation
    origin_tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # tenant_id is NULL while status == 'pending_claim', and set to the claiming tenant once active
    tenant_id = Column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # assigned_user_id is the specific staff/agent assigned
    assigned_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Allowed statuses: 'pending_claim', 'active', 'closed'
    status = Column(String(20), nullable=False, default="pending_claim", index=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    claimed_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    tenant = relationship("Tenant", foreign_keys=[tenant_id], back_populates="cases")
    origin_tenant = relationship("Tenant", foreign_keys=[origin_tenant_id])
    assigned_user = relationship("User", foreign_keys=[assigned_user_id], back_populates="assigned_cases")

    __table_args__ = (
        # Partial unique index ensuring a tenant cannot have multiple active cases for the same VIN simultaneously
        Index(
            "uq_tenant_active_vin",
            "tenant_id",
            "vin",
            unique=True,
            postgresql_where=text("status = 'active'"),
            sqlite_where=text("status = 'active'"),
        ),
        # Composite index for rapid lookup during scan ingestion
        Index("ix_case_tenant_vin_status", "tenant_id", "vin", "status"),
    )
