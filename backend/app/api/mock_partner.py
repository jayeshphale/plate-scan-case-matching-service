from fastapi import APIRouter
from pydantic import BaseModel, Field
from app.services.eligibility_service import eligibility_service

router = APIRouter(prefix="/mock/partner-network", tags=["Mock Partner Network"])


class EligibilityRequest(BaseModel):
    vin: str = Field(..., description="Vehicle Identification Number")


class EligibilityResponse(BaseModel):
    vin: str
    still_eligible_for_repo: bool


@router.post(
    "/eligibility",
    response_model=EligibilityResponse,
    summary="Mock partner repossession eligibility check",
    description="Simulates an external lender/forwarder partner network checking repossession eligibility.",
)
async def check_repo_eligibility(req: EligibilityRequest):
    """Stub endpoint simulating partner network API."""
    is_eligible = await eligibility_service.check_eligibility(req.vin)
    return EligibilityResponse(
        vin=req.vin,
        still_eligible_for_repo=is_eligible,
    )
