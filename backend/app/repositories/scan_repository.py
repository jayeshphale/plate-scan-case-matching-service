from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import asc
from app.models.scan import Scan


class ScanRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        camera_id: str,
        plate: str,
        vin: str,
        latitude: float,
        longitude: float,
        scanned_at: datetime,
        image_url: Optional[str] = None,
    ) -> Scan:
        """Persist every incoming scan into the database."""
        scan = Scan(
            camera_id=camera_id,
            plate=plate,
            vin=vin,
            latitude=latitude,
            longitude=longitude,
            scanned_at=scanned_at,
            image_url=image_url,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)
        return scan

    def get_scans_by_vin(self, vin: str) -> List[Scan]:
        """Fetch all chronological scans for a VIN to generate the location trail."""
        return (
            self.db.query(Scan)
            .filter(Scan.vin == vin)
            .order_by(asc(Scan.scanned_at))
            .all()
        )
