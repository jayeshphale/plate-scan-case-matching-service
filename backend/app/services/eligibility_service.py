import logging
from abc import ABC, abstractmethod
from typing import Set
import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


class BaseEligibilityService(ABC):
    """Abstract interface for repossession eligibility verification."""

    @abstractmethod
    async def check_eligibility(self, vin: str) -> bool:
        """Check if vehicle with VIN is still eligible for repossession."""
        pass


class MockEligibilityService(BaseEligibilityService):
    """Deterministic mock eligibility service for case study and testing.
    
    In a real production environment, this is swapped via dependency injection
    with an HTTP client communicating with the lender/forwarder partner network.
    """

    # Pre-configured eligible VINs according to case study spec
    ELIGIBLE_VINS: Set[str] = {
        "5NPE34AF9KH123456",  # Spec scenario: Tenant B scan creates pending_claim
        "1FTFW1E51NFA12345",  # Spec scenario: Tenant A active case VIN
        "2C3CDXBG4KH987654",  # Additional test VIN
        "3VW2B7AJ5HM555555",  # Additional test VIN
    }

    def __init__(self, external_url: str = None):
        self.external_url = external_url or settings.ELIGIBILITY_SERVICE_URL

    async def check_eligibility(self, vin: str) -> bool:
        """Check eligibility deterministically or via HTTP if external URL is set."""
        logger.info(f"Checking repossession eligibility for VIN: {vin}")
        
        # Check deterministic list or test prefix
        if vin in self.ELIGIBLE_VINS or vin.endswith("ELIGIBLE") or vin.startswith("5NPE"):
            logger.info(f"VIN {vin} is eligible for repossession (deterministic match)")
            return True

        # Default fallback for unconfigured VINs
        logger.info(f"VIN {vin} is not eligible for repossession")
        return False


# Singleton service instance
eligibility_service = MockEligibilityService()
