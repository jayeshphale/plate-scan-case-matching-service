import logging
from typing import Optional, List
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.case import Case
from app.models.user import User
from app.models.scan import Scan
from app.schemas.case import CaseResponse, CaseListResponse
from app.repositories.case_repository import CaseRepository
from app.repositories.scan_repository import ScanRepository

logger = logging.getLogger(__name__)


class CaseService:
    def __init__(self, db: Session):
        self.db = db
        self.case_repo = CaseRepository(db)
        self.scan_repo = ScanRepository(db)

    def _to_case_response(self, case: Case) -> CaseResponse:
        """Helper to serialize Case entity with joined relations into CaseResponse."""
        return CaseResponse(
            id=case.id,
            vin=case.vin,
            origin_tenant_id=case.origin_tenant_id,
            origin_tenant_name=case.origin_tenant.name if case.origin_tenant else None,
            tenant_id=case.tenant_id,
            tenant_name=case.tenant.name if case.tenant else None,
            assigned_user_id=case.assigned_user_id,
            assigned_user_name=case.assigned_user.username if case.assigned_user else None,
            status=case.status,
            created_at=case.created_at,
            updated_at=case.updated_at,
            claimed_at=case.claimed_at,
            closed_at=case.closed_at,
        )

    def claim_case(self, case_id: str, claiming_user: User) -> CaseResponse:
        """Atomically claim a pending case.
        
        Uses row-level locking (SELECT FOR UPDATE) within an isolated transaction.
        If the case has already been claimed (active) or closed, raises HTTP 409 Conflict.
        """
        logger.info(f"User {claiming_user.username} (tenant={claiming_user.tenant_id}) attempting to claim case {case_id}")

        # Use row lock to prevent concurrent claim race conditions
        case = self.case_repo.get_by_id_for_update(case_id)
        if not case:
            logger.warning(f"Claim failed: Case {case_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )

        # Race condition verification: only pending_claim cases can be claimed
        if case.status != "pending_claim":
            logger.warning(f"Claim conflict: Case {case_id} already has status '{case.status}'")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Case has already been claimed",
            )

        # Check if claiming tenant already has an active case for this VIN (partial unique constraint)
        existing_active = self.case_repo.find_active_by_tenant_and_vin(claiming_user.tenant_id, case.vin)
        if existing_active:
            logger.warning(f"Claim rejected: Tenant {claiming_user.tenant_id} already has active case for VIN {case.vin}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Your agency already has an active case for this VIN",
            )

        try:
            updated_case = self.case_repo.claim_case(case, claiming_user)
        except Exception as e:
            self.db.rollback()
            logger.error(f"Transaction conflict claiming case {case_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Case has already been claimed",
            )

        logger.info(f"Case {case_id} successfully claimed by tenant {claiming_user.tenant_id}")
        
        # Reload with relations for clean response
        loaded_case = self.case_repo.get_by_id(updated_case.id)
        return self._to_case_response(loaded_case)

    def get_case_scans(self, case_id: str, current_user: User) -> List[Scan]:
        """Retrieve location trail (all chronological scans for the case's VIN).
        
        Strict tenant access rule:
        - If status == 'pending_claim', accessible to any authenticated user.
        - If status in ('active', 'closed'), ONLY accessible to users of owning tenant.
        """
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )

        # Tenant isolation check
        if case.status != "pending_claim" and case.tenant_id != current_user.tenant_id:
            logger.warning(f"Access denied: User {current_user.username} (tenant {current_user.tenant_id}) tried accessing case {case_id} owned by tenant {case.tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this case",
            )

        # Query all historical scans for this VIN ordered by scanned_at ASC
        return self.scan_repo.get_scans_by_vin(case.vin)

    def get_case_by_id(self, case_id: str, current_user: User) -> CaseResponse:
        """Fetch individual case by ID with tenant access enforcement."""
        case = self.case_repo.get_by_id(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )

        # Tenant isolation check
        if case.status != "pending_claim" and case.tenant_id != current_user.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this case",
            )

        return self._to_case_response(case)

    def list_cases(
        self,
        current_user: User,
        status: Optional[str] = None,
        vin: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> CaseListResponse:
        """List cases with tenant isolation:
        - Returns current user's tenant cases at all statuses
        - PLUS pending_claim cases from ANY tenant
        """
        cases, total = self.case_repo.list_accessible_cases(
            current_tenant_id=current_user.tenant_id,
            status_filter=status,
            vin_filter=vin,
            page=page,
            page_size=page_size,
        )

        items = [self._to_case_response(c) for c in cases]
        return CaseListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )
