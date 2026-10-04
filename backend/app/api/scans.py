from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.scan import ScanCreate, ScanIngestResponse
from app.services.scan_service import ScanService

router = APIRouter(prefix="/scans", tags=["Scans"])


@router.post(
    "",
    response_model=ScanIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest a license plate scan (camera webhook)",
    description=(
        "Simulates a camera webhook ingestion. Unauthenticated call. "
        "The camera_id is used to resolve the camera and owning tenant. "
        "The scan is unconditionally stored. Then the service checks for an active case "
        "matching the tenant + VIN (Flow A) or invokes repossession eligibility to create "
        "a pending_claim case (Flow B)."
    ),
)
async def ingest_scan(
    scan_in: ScanCreate,
    db: Session = Depends(get_db),
):
    """Camera webhook ingestion endpoint."""
    scan_service = ScanService(db=db)
    return await scan_service.ingest_scan(scan_in)
