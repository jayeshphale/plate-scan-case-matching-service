import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.camera import Camera
from app.models.case import Case
from app.models.scan import Scan
from app.schemas.scan import ScanCreate, ScanIngestResponse
from app.repositories.scan_repository import ScanRepository
from app.repositories.case_repository import CaseRepository
from app.services.eligibility_service import BaseEligibilityService, eligibility_service

logger = logging.getLogger(__name__)


class ScanService:
    def __init__(
        self,
        db: Session,
        eligibility_svc: BaseEligibilityService = eligibility_service,
    ):
        self.db = db
        self.scan_repo = ScanRepository(db)
        self.case_repo = CaseRepository(db)
        self.eligibility_svc = eligibility_svc

    async def ingest_scan(self, scan_in: ScanCreate) -> ScanIngestResponse:
        """Process an inbound camera scan webhook:
        1. Resolve camera and tenant. Reject unknown/inactive cameras.
        2. Always persist scan in database.
        3. Check for active case for tenant + VIN (Flow A).
        4. If not found, check repossession eligibility and create pending_claim case if eligible (Flow B).
        """
        logger.info(f"Received scan for plate={scan_in.plate}, vin={scan_in.vin}, camera_id={scan_in.camera_id}")

        # 1. Resolve camera
        camera = self.db.query(Camera).filter(Camera.camera_id == scan_in.camera_id).first()
        if not camera:
            logger.warning(f"Scan rejected: Unknown camera '{scan_in.camera_id}'")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Camera with identifier '{scan_in.camera_id}' not found",
            )
        
        if not camera.is_active:
            logger.warning(f"Scan rejected: Camera '{scan_in.camera_id}' is inactive")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Camera '{scan_in.camera_id}' is deactivated",
            )

        resolved_tenant_id = camera.tenant_id

        # 2. Always store the scan regardless of matching
        scan = self.scan_repo.create(
            camera_id=scan_in.camera_id,
            plate=scan_in.plate,
            vin=scan_in.vin,
            latitude=scan_in.latitude,
            longitude=scan_in.longitude,
            scanned_at=scan_in.scanned_at,
            image_url=scan_in.image_url,
        )
        logger.info(f"Scan successfully persisted with id={scan.id}")

        # 3. Flow A: Search for active case for this tenant + VIN
        active_case = self.case_repo.find_active_by_tenant_and_vin(
            tenant_id=resolved_tenant_id,
            vin=scan_in.vin,
        )

        if active_case:
            logger.info(f"Flow A: Scan matched active case id={active_case.id} for tenant={resolved_tenant_id}")
            return ScanIngestResponse(
                scan_id=scan.id,
                tenant_id=resolved_tenant_id,
                vin=scan_in.vin,
                matched_existing_case=True,
                created_new_case=False,
                case_id=active_case.id,
                case_status=active_case.status,
                message="Scan recorded and matched to existing active case location trail.",
            )

        # 4. Flow B: No active case for this tenant. Call external eligibility service
        is_eligible = await self.eligibility_svc.check_eligibility(scan_in.vin)

        if is_eligible:
            # Check if an unassigned pending_claim case already exists for this VIN (idempotency)
            pending_case = self.case_repo.find_pending_by_vin(scan_in.vin)
            if pending_case:
                logger.info(f"Flow B: Eligible vehicle already has pending_claim case id={pending_case.id}")
                return ScanIngestResponse(
                    scan_id=scan.id,
                    tenant_id=resolved_tenant_id,
                    vin=scan_in.vin,
                    matched_existing_case=False,
                    created_new_case=False,
                    case_id=pending_case.id,
                    case_status=pending_case.status,
                    message="Scan recorded. Existing pending claim case updated with new sighting.",
                )

            # Create new case in pending_claim status
            new_case = self.case_repo.create(
                vin=scan_in.vin,
                origin_tenant_id=resolved_tenant_id,
                tenant_id=None,  # Not owned by any tenant until claimed
                assigned_user_id=None,
                status="pending_claim",
            )
            logger.info(f"Flow B: Created new pending_claim case id={new_case.id} originated from tenant={resolved_tenant_id}")
            return ScanIngestResponse(
                scan_id=scan.id,
                tenant_id=resolved_tenant_id,
                vin=scan_in.vin,
                matched_existing_case=False,
                created_new_case=True,
                case_id=new_case.id,
                case_status="pending_claim",
                message="Vehicle eligible for repossession. New pending claim case created.",
            )

        # Vehicle not eligible
        logger.info(f"Scan recorded for VIN {scan_in.vin}. Vehicle is not eligible for repossession.")
        return ScanIngestResponse(
            scan_id=scan.id,
            tenant_id=resolved_tenant_id,
            vin=scan_in.vin,
            matched_existing_case=False,
            created_new_case=False,
            case_id=None,
            case_status=None,
            message="Scan recorded in history. Vehicle is not eligible for repossession.",
        )
