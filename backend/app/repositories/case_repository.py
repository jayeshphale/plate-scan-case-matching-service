from typing import Optional, List, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, desc, asc
from app.models.case import Case
from app.models.user import User


class CaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, case_id: str) -> Optional[Case]:
        """Fetch a case by ID with related tenant and user information."""
        return (
            self.db.query(Case)
            .options(
                joinedload(Case.tenant),
                joinedload(Case.origin_tenant),
                joinedload(Case.assigned_user),
            )
            .filter(Case.id == case_id)
            .first()
        )

    def get_by_id_for_update(self, case_id: str) -> Optional[Case]:
        """Fetch case by ID with row-level lock (FOR UPDATE) to prevent race conditions during claim."""
        query = self.db.query(Case).filter(Case.id == case_id)
        # SQLAlchemy supports with_for_update; SQLite ignores it gracefully or handles via db lock
        try:
            query = query.with_for_update()
        except Exception:
            pass
        return query.first()

    def find_active_by_tenant_and_vin(self, tenant_id: str, vin: str) -> Optional[Case]:
        """Find an active case belonging to the specified tenant for a given VIN."""
        return (
            self.db.query(Case)
            .filter(
                Case.tenant_id == tenant_id,
                Case.vin == vin,
                Case.status == "active",
            )
            .first()
        )

    def find_pending_by_vin(self, vin: str) -> Optional[Case]:
        """Find an existing pending_claim case for a VIN (for deduplication/idempotency)."""
        return (
            self.db.query(Case)
            .filter(
                Case.vin == vin,
                Case.status == "pending_claim",
            )
            .first()
        )

    def create(
        self,
        vin: str,
        origin_tenant_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        assigned_user_id: Optional[str] = None,
        status: str = "pending_claim",
    ) -> Case:
        """Create a new case in the database."""
        case = Case(
            vin=vin,
            origin_tenant_id=origin_tenant_id,
            tenant_id=tenant_id,
            assigned_user_id=assigned_user_id,
            status=status,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case

    def claim_case(self, case: Case, claiming_user: User) -> Case:
        """Assign pending case to claiming user's tenant and mark active."""
        now = datetime.now(timezone.utc)
        case.status = "active"
        case.tenant_id = claiming_user.tenant_id
        case.assigned_user_id = claiming_user.id
        case.claimed_at = now
        case.updated_at = now
        self.db.commit()
        self.db.refresh(case)
        return case

    def list_accessible_cases(
        self,
        current_tenant_id: str,
        status_filter: Optional[str] = None,
        vin_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Case], int]:
        """List cases with strict tenant isolation:
        - Authenticated user sees:
          1. Their own tenant's cases (any status)
          2. pending_claim cases from ANY tenant
        - Other tenants' active and closed cases are strictly excluded.
        """
        # Base tenant visibility filter: own cases OR globally claimable pending cases
        base_condition = or_(
            Case.tenant_id == current_tenant_id,
            Case.status == "pending_claim",
        )

        query = self.db.query(Case).options(
            joinedload(Case.tenant),
            joinedload(Case.origin_tenant),
            joinedload(Case.assigned_user),
        ).filter(base_condition)

        if status_filter:
            query = query.filter(Case.status == status_filter)

        if vin_filter:
            query = query.filter(Case.vin == vin_filter)

        total = query.count()
        
        offset = (page - 1) * page_size
        items = query.order_by(desc(Case.created_at)).offset(offset).limit(page_size).all()
        return items, total
