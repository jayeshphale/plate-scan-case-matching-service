from datetime import datetime, timezone
from app.models.scan import Scan
from app.models.case import Case


def test_scan_unknown_camera(client, seed_test_data):
    """Test scan with unassigned camera_id is rejected with 404."""
    payload = {
        "camera_id": "cam_unknown_999",
        "plate": "TEST1234",
        "vin": "VINUNKNOWN000000",
        "latitude": 33.7490,
        "longitude": -84.3880,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "image_url": "https://example.com/test.jpg",
    }
    response = client.post("/api/v1/scans", json=payload)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_scan_inactive_camera(client, seed_test_data):
    """Test scan from deactivated camera is rejected with 400."""
    payload = {
        "camera_id": "cam_disabled",
        "plate": "TEST1234",
        "vin": "VINDISABLED0000",
        "latitude": 33.7490,
        "longitude": -84.3880,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }
    response = client.post("/api/v1/scans", json=payload)
    assert response.status_code == 400
    assert "deactivated" in response.json()["detail"]


def test_scan_existing_case_flow_a(client, seed_test_data, db_session):
    """Test Flow A: Scan arrives from cam_1001 for VIN 1FTFW1E51NFA12345 (which Tenant A already has active case for).
    Expected:
    - Scan is stored
    - Existing active case matched
    - No new case created
    - Scan appears in location trail
    """
    initial_scan_count = db_session.query(Scan).filter(Scan.vin == "1FTFW1E51NFA12345").count()
    
    payload = {
        "camera_id": "cam_1001",
        "plate": "7XYZ123",
        "vin": "1FTFW1E51NFA12345",
        "latitude": 33.7500,
        "longitude": -84.3900,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "image_url": "https://example.com/new_sight.jpg",
    }
    response = client.post("/api/v1/scans", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["matched_existing_case"] is True
    assert data["created_new_case"] is False
    assert data["case_id"] == "case-a-active-uuid"
    assert data["case_status"] == "active"
    assert data["tenant_id"] == "tenant-a-uuid"

    # Verify scan was stored
    scans_now = db_session.query(Scan).filter(Scan.vin == "1FTFW1E51NFA12345").count()
    assert scans_now == initial_scan_count + 1


def test_scan_new_case_flow_b_eligible(client, seed_test_data, db_session):
    """Test Flow B: Scan arrives from cam_2050 for an eligible VIN with no existing case.
    Expected:
    - Scan is stored
    - Eligibility service returns true
    - New pending_claim case created
    - Case has origin_tenant_id = cam_2050's tenant, but tenant_id is NULL (unclaimed)
    """
    new_vin = "5NPE34AF9KH_NEW" + "_ELIGIBLE"
    payload = {
        "camera_id": "cam_2050",
        "plate": "NEWPLATE1",
        "vin": new_vin,
        "latitude": 34.0522,
        "longitude": -118.2437,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "image_url": "https://example.com/new_car.jpg",
    }
    response = client.post("/api/v1/scans", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["matched_existing_case"] is False
    assert data["created_new_case"] is True
    assert data["case_status"] == "pending_claim"
    assert data["case_id"] is not None

    # Verify in DB
    created_case = db_session.query(Case).filter(Case.id == data["case_id"]).first()
    assert created_case is not None
    assert created_case.vin == new_vin
    assert created_case.status == "pending_claim"
    assert created_case.tenant_id is None
    assert created_case.origin_tenant_id == "tenant-b-uuid"


def test_scan_ineligible_stored_without_case(client, seed_test_data, db_session):
    """Test that scans for ineligible vehicles are still permanently stored in history,
    without creating a case.
    """
    ineligible_vin = "INELIGIBLE_VIN_12345"
    payload = {
        "camera_id": "cam_1001",
        "plate": "NOTELG1",
        "vin": ineligible_vin,
        "latitude": 33.7490,
        "longitude": -84.3880,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
    }
    response = client.post("/api/v1/scans", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["matched_existing_case"] is False
    assert data["created_new_case"] is False
    assert data["case_id"] is None

    # Scan MUST still be stored
    stored_scan = db_session.query(Scan).filter(Scan.vin == ineligible_vin).first()
    assert stored_scan is not None
    assert stored_scan.plate == "NOTELG1"
