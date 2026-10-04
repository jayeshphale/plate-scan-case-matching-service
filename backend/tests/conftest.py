import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings
from app.db.database import Base, get_db
from app.main import app
from app.models.tenant import Tenant
from app.models.user import User
from app.models.camera import Camera
from app.models.case import Case
from app.models.scan import Scan
from app.core.security import get_password_hash, create_access_token

# Use in-memory SQLite database with StaticPool for fast, isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test function."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient using the isolated test database session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_test_data(db_session):
    """Seed test fixtures with two distinct recovery agency tenants and users."""
    # Tenant A
    tenant_a = Tenant(id="tenant-a-uuid", name="Agency Alpha")
    # Tenant B
    tenant_b = Tenant(id="tenant-b-uuid", name="Agency Bravo")
    db_session.add_all([tenant_a, tenant_b])
    db_session.flush()

    pw_hash = get_password_hash("password123")
    user_a = User(
        id="user-a-uuid",
        tenant_id=tenant_a.id,
        username="user_a",
        email="user_a@agency-a.com",
        password_hash=pw_hash,
        role="staff",
        is_active=True,
    )
    user_b = User(
        id="user-b-uuid",
        tenant_id=tenant_b.id,
        username="user_b",
        email="user_b@agency-b.com",
        password_hash=pw_hash,
        role="staff",
        is_active=True,
    )
    db_session.add_all([user_a, user_b])
    db_session.flush()

    # Cameras
    cam_a = Camera(
        id="cam-a-uuid",
        camera_id="cam_1001",
        tenant_id=tenant_a.id,
        name="Truck A Cam",
        is_active=True,
    )
    cam_b = Camera(
        id="cam-b-uuid",
        camera_id="cam_2050",
        tenant_id=tenant_b.id,
        name="Truck B Cam",
        is_active=True,
    )
    cam_inactive = Camera(
        id="cam-inactive-uuid",
        camera_id="cam_disabled",
        tenant_id=tenant_a.id,
        name="Broken Cam",
        is_active=False,
    )
    db_session.add_all([cam_a, cam_b, cam_inactive])
    db_session.flush()

    # Active Case for Tenant A
    now = datetime.now(timezone.utc)
    case_a_active = Case(
        id="case-a-active-uuid",
        vin="1FTFW1E51NFA12345",
        origin_tenant_id=tenant_a.id,
        tenant_id=tenant_a.id,
        assigned_user_id=user_a.id,
        status="active",
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=1),
        claimed_at=now - timedelta(days=2),
    )
    # Closed Case for Tenant B
    case_b_closed = Case(
        id="case-b-closed-uuid",
        vin="CLOSEDVIN999999",
        origin_tenant_id=tenant_b.id,
        tenant_id=tenant_b.id,
        assigned_user_id=user_b.id,
        status="closed",
        created_at=now - timedelta(days=10),
        updated_at=now - timedelta(days=3),
        closed_at=now - timedelta(days=3),
    )
    # Pending Case originated by Tenant B
    case_pending = Case(
        id="case-pending-uuid",
        vin="5NPE34AF9KH123456",
        origin_tenant_id=tenant_b.id,
        tenant_id=None,
        assigned_user_id=None,
        status="pending_claim",
        created_at=now - timedelta(hours=3),
        updated_at=now - timedelta(hours=3),
    )
    db_session.add_all([case_a_active, case_b_closed, case_pending])
    db_session.flush()

    # Historical scans for Tenant A's active case
    scan1 = Scan(
        camera_id="cam_1001",
        plate="7XYZ123",
        vin="1FTFW1E51NFA12345",
        latitude=33.7480,
        longitude=-84.3870,
        scanned_at=now - timedelta(hours=10),
    )
    scan2 = Scan(
        camera_id="cam_1001",
        plate="7XYZ123",
        vin="1FTFW1E51NFA12345",
        latitude=33.7490,
        longitude=-84.3880,
        scanned_at=now - timedelta(hours=5),
    )
    db_session.add_all([scan1, scan2])
    db_session.commit()

    return {
        "tenant_a": tenant_a,
        "tenant_b": tenant_b,
        "user_a": user_a,
        "user_b": user_b,
        "cam_a": cam_a,
        "cam_b": cam_b,
        "case_a_active": case_a_active,
        "case_b_closed": case_b_closed,
        "case_pending": case_pending,
    }


@pytest.fixture
def auth_headers_a(seed_test_data):
    """Authorization headers for Tenant A staff user."""
    user = seed_test_data["user_a"]
    token = create_access_token({"sub": user.id, "tenant_id": user.tenant_id, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_b(seed_test_data):
    """Authorization headers for Tenant B staff user."""
    user = seed_test_data["user_b"]
    token = create_access_token({"sub": user.id, "tenant_id": user.tenant_id, "role": user.role})
    return {"Authorization": f"Bearer {token}"}
