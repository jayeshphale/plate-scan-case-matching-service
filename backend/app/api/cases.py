from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.dependencies import get_current_user, require_staff
from app.models.user import User
from app.schemas.case import CaseResponse, CaseListResponse
from app.schemas.scan import ScanResponse
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["Cases"])


@router.get(
    "",
    response_model=CaseListResponse,
    summary="List accessible cases for authenticated user's tenant",
    description=(
        "Returns the caller's own tenant's cases at every status, plus pending_claim "
        "cases from ANY tenant (so they can be claimed). Active and closed cases outside "
        "the caller's tenant are strictly excluded."
    ),
)
def list_cases(
    status: Optional[str] = Query(None, description="Filter by case status (pending_claim, active, closed)"),
    vin: Optional[str] = Query(None, description="Filter by VIN"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve filtered and paginated cases scoped to the user's tenant isolation rules."""
    case_service = CaseService(db)
    return case_service.list_cases(
        current_user=current_user,
        status=status,
        vin=vin,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
    summary="Get case details",
    description="Retrieve details for a specific case, verifying tenant access authorization.",
)
def get_case(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get single case by ID with tenant access control."""
    case_service = CaseService(db)
    return case_service.get_case_by_id(case_id, current_user)


@router.post(
    "/{case_id}/claim",
    response_model=CaseResponse,
    summary="Claim a pending case",
    description=(
        "Cross-tenant claiming endpoint: Authenticated staff from ANY tenant can claim "
        "a pending_claim case. Assigns the case to the user's tenant, sets assigned_user_id, "
        "and transitions status to active. If the case is already active or closed, returns HTTP 409."
    ),
)
def claim_case(
    case_id: str,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
):
    """Claim a pending case atomically with row locking."""
    case_service = CaseService(db)
    return case_service.claim_case(case_id, current_user)


@router.get(
    "/{case_id}/scans",
    response_model=List[ScanResponse],
    summary="Get scan history / location trail for a case's VIN",
    description=(
        "Returns all scans on record for the case's VIN ordered chronologically by scanned_at. "
        "Accessible to any authenticated user if the case is pending_claim, or restricted "
        "strictly to the owning tenant if active/closed."
    ),
)
def get_case_scans(
    case_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve chronological sighting trail for the case's vehicle."""
    case_service = CaseService(db)
    return case_service.get_case_scans(case_id, current_user)
