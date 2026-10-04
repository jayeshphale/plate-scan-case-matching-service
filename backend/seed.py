import sys
import logging
from datetime import datetime, timezone, timedelta
from app.db.database import SessionLocal, Base, engine
from app.models.tenant import Tenant
from app.models.user import User
from app.models.camera import Camera
from app.models.case import Case
from app.models.scan import Scan
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


def seed_database(reset: bool = False):
    """Seed the database with tenants, users, cameras, cases, and historical scans."""
    if reset:
        logger.info("Resetting all database tables...")
        Base.metadata.drop_all(bind=engine)

    logger.info("Creating tables if they do not exist...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded (idempotency check)
        existing_tenant = db.query(Tenant).filter(Tenant.name == "Recovery Agency A").first()
        if existing_tenant and not reset:
            logger.info("Database is already seeded. Skipping initial seeding (idempotent).")
            return

        logger.info("Seeding Tenants...")
        tenant_a = Tenant(name="Recovery Agency A")
        tenant_b = Tenant(name="Recovery Agency B")
        db.add_all([tenant_a, tenant_b])
        db.flush()

        logger.info("Seeding Users...")
        default_pw_hash = get_password_hash("password123")
        
        user_a_staff = User(
            tenant_id=tenant_a.id,
            username="tenant_a_user",
            email="staff@agency-a.example.com",
            password_hash=default_pw_hash,
            role="staff",
        )
        user_a_admin = User(
            tenant_id=tenant_a.id,
            username="tenant_a_admin",
            email="admin@agency-a.example.com",
            password_hash=default_pw_hash,
            role="admin",
        )
        user_b_staff = User(
            tenant_id=tenant_b.id,
            username="tenant_b_user",
            email="staff@agency-b.example.com",
            password_hash=default_pw_hash,
            role="staff",
        )
        user_b_admin = User(
            tenant_id=tenant_b.id,
            username="tenant_b_admin",
            email="admin@agency-b.example.com",
            password_hash=default_pw_hash,
            role="admin",
        )
        db.add_all([user_a_staff, user_a_admin, user_b_staff, user_b_admin])
        db.flush()

        logger.info("Seeding Cameras...")
        cam_1001 = Camera(
            camera_id="cam_1001",
            tenant_id=tenant_a.id,
            name="Truck Alpha Camera",
            truck_identifier="TRUCK-A01",
            is_active=True,
        )
        cam_2050 = Camera(
            camera_id="cam_2050",
            tenant_id=tenant_b.id,
            name="Truck Bravo Camera",
            truck_identifier="TRUCK-B02",
            is_active=True,
        )
        db.add_all([cam_1001, cam_2050])
        db.flush()

        logger.info("Seeding Active Case for Tenant A (VIN: 1FTFW1E51NFA12345)...")
        now = datetime.now(timezone.utc)
        case_a = Case(
            vin="1FTFW1E51NFA12345",
            origin_tenant_id=tenant_a.id,
            tenant_id=tenant_a.id,
            assigned_user_id=user_a_staff.id,
            status="active",
            created_at=now - timedelta(days=5),
            updated_at=now - timedelta(days=1),
            claimed_at=now - timedelta(days=5),
        )
        db.add(case_a)
        db.flush()

        logger.info("Seeding Historical Scans for Tenant A's Active Case...")
        # 3 historical sightings at different locations and timestamps
        scan1 = Scan(
            camera_id="cam_1001",
            plate="7XYZ123",
            vin="1FTFW1E51NFA12345",
            latitude=33.7480,
            longitude=-84.3870,
            scanned_at=now - timedelta(days=4),
            image_url="https://images.unsplash.com/photo-1549399542-7e3f8b79c341?w=400",
        )
        scan2 = Scan(
            camera_id="cam_1001",
            plate="7XYZ123",
            vin="1FTFW1E51NFA12345",
            latitude=33.7485,
            longitude=-84.3875,
            scanned_at=now - timedelta(days=2),
            image_url="https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=400",
        )
        scan3 = Scan(
            camera_id="cam_1001",
            plate="7XYZ123",
            vin="1FTFW1E51NFA12345",
            latitude=33.7490,
            longitude=-84.3880,
            scanned_at=now - timedelta(hours=12),
            image_url="https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=400",
        )
        db.add_all([scan1, scan2, scan3])

        logger.info("Seeding an initial cross-tenant pending_claim case originated from Tenant B...")
        # This provides an immediate pending claim to view in the dashboard
        pending_case = Case(
            vin="2C3CDXBG4KH987654",
            origin_tenant_id=tenant_b.id,
            tenant_id=None,
            assigned_user_id=None,
            status="pending_claim",
            created_at=now - timedelta(hours=6),
            updated_at=now - timedelta(hours=6),
        )
        db.add(pending_case)
        db.flush()

        pending_scan = Scan(
            camera_id="cam_2050",
            plate="4ABC999",
            vin="2C3CDXBG4KH987654",
            latitude=34.0522,
            longitude=-118.2437,
            scanned_at=now - timedelta(hours=6),
            image_url="https://images.unsplash.com/photo-1580273916550-e323be2ae537?w=400",
        )
        db.add(pending_scan)

        db.commit()
        logger.info("Database seeding completed successfully!")
        logger.info("Demo credentials created:")
        logger.info("Tenant A (Recovery Agency A): username='tenant_a_user', password='password123'")
        logger.info("Tenant B (Recovery Agency B): username='tenant_b_user', password='password123'")

    except Exception as e:
        logger.error(f"Error during database seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_flag = "--reset" in sys.argv
    seed_database(reset=reset_flag)
