"""Verification script testing the exact 3 demo scenarios from the assignment specification.
Can be executed to verify end-to-end functionality via HTTP/FastAPI TestClient.
"""
import sys
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import SessionLocal, Base, engine
from seed import seed_database

def run_scenarios():
    print("=" * 70)
    print("DEMO VERIFICATION: Plate Scan & Case Matching Service")
    print("=" * 70)
    
    # 1. Reset and reseed database
    print("\n[Step 0] Initializing & Seeding Database...")
    Base.metadata.drop_all(bind=engine)
    seed_database()
    
    client = TestClient(app)

    # Scenario 1: Existing Case Flow
    print("\n" + "-" * 70)
    print("SCENARIO 1: Existing Case Flow (Flow A)")
    print("-" * 70)
    print("1. Logging in as Tenant A (tenant_a_user)...")
    login_a_res = client.post("/api/v1/auth/login", json={"username": "tenant_a_user", "password": "password123"})
    assert login_a_res.status_code == 200, f"Login failed: {login_a_res.text}"
    token_a = login_a_res.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}
    print("   -> Logged in successfully. Tenant: Recovery Agency A")

    print("\n2. Ingesting scan from cam_1001 for active VIN 1FTFW1E51NFA12345...")
    scan_payload_1 = {
        "camera_id": "cam_1001",
        "plate": "7XYZ123",
        "vin": "1FTFW1E51NFA12345",
        "latitude": 33.7490,
        "longitude": -84.3880,
        "scanned_at": "2026-09-01T14:32:00Z",
        "image_url": "https://example.com/scans/img_88213.jpg"
    }
    scan_res_1 = client.post("/api/v1/scans", json=scan_payload_1)
    assert scan_res_1.status_code == 201, f"Scan failed: {scan_res_1.text}"
    data_1 = scan_res_1.json()
    print("   -> Scan Result:")
    print(f"      - Scan ID: {data_1['scan_id']}")
    print(f"      - Matched Existing Case: {data_1['matched_existing_case']}")
    print(f"      - Created New Case: {data_1['created_new_case']}")
    print(f"      - Case ID: {data_1['case_id']}")
    print(f"      - Case Status: {data_1['case_status']}")
    assert data_1["matched_existing_case"] is True
    assert data_1["created_new_case"] is False
    assert data_1["case_status"] == "active"
    matched_case_id = data_1["case_id"]

    print("\n3. Verifying scan appears in case's location trail...")
    scans_res = client.get(f"/api/v1/cases/{matched_case_id}/scans", headers=headers_a)
    assert scans_res.status_code == 200
    trail = scans_res.json()
    print(f"   -> Location trail contains {len(trail)} sightings chronologically ordered.")
    assert len(trail) >= 4  # 3 seeded + 1 newly ingested
    print("   -> Scenario 1 PASSED: Scan stored, existing active case matched, location trail updated.")

    # Scenario 2: New Case Flow
    print("\n" + "-" * 70)
    print("SCENARIO 2: New Case Flow (Flow B)")
    print("-" * 70)
    print("1. Ingesting scan from cam_2050 for VIN 5NPE34AF9KH123456 (no existing case)...")
    scan_payload_2 = {
        "camera_id": "cam_2050",
        "plate": "2MNO456",
        "vin": "5NPE34AF9KH123456",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "scanned_at": "2026-09-02T10:00:00Z",
        "image_url": "https://example.com/scans/img_new_repo.jpg"
    }
    scan_res_2 = client.post("/api/v1/scans", json=scan_payload_2)
    assert scan_res_2.status_code == 201, f"Scan 2 failed: {scan_res_2.text}"
    data_2 = scan_res_2.json()
    print("   -> Scan Result:")
    print(f"      - Scan ID: {data_2['scan_id']}")
    print(f"      - Matched Existing Case: {data_2['matched_existing_case']}")
    print(f"      - Created New Case: {data_2['created_new_case']}")
    print(f"      - New Case ID: {data_2['case_id']}")
    print(f"      - Case Status: {data_2['case_status']}")
    assert data_2["matched_existing_case"] is False
    assert data_2["created_new_case"] is True
    assert data_2["case_status"] == "pending_claim"
    new_pending_case_id = data_2["case_id"]
    print("   -> Scenario 2 PASSED: Vehicle verified eligible, new pending_claim case created.")

    # Scenario 3: Cross-Tenant Claim
    print("\n" + "-" * 70)
    print("SCENARIO 3: Cross-Tenant Claim")
    print("-" * 70)
    print("1. Checking Tenant A's visible pending cases...")
    pending_list_res = client.get("/api/v1/cases?status=pending_claim", headers=headers_a)
    assert pending_list_res.status_code == 200
    pending_items = pending_list_res.json()["items"]
    pending_ids = [item["id"] for item in pending_items]
    assert new_pending_case_id in pending_ids, "Newly created pending case should be visible to Tenant A!"
    print(f"   -> Tenant A can see pending claim {new_pending_case_id} originated by Tenant B.")

    print("\n2. Tenant A claims the pending case...")
    claim_res = client.post(f"/api/v1/cases/{new_pending_case_id}/claim", headers=headers_a)
    assert claim_res.status_code == 200, f"Claim failed: {claim_res.text}"
    claim_data = claim_res.json()
    print("   -> Claim Result:")
    print(f"      - Status: {claim_data['status']}")
    print(f"      - Assigned Tenant: {claim_data['tenant_name']}")
    print(f"      - Assigned User: {claim_data['assigned_user_name']}")
    print(f"      - Claimed At: {claim_data['claimed_at']}")
    assert claim_data["status"] == "active"
    assert claim_data["tenant_name"] == "Recovery Agency A"
    assert claim_data["assigned_user_name"] == "tenant_a_user"

    print("\n3. Verifying Tenant B can NO LONGER claim or see this case as pending...")
    login_b_res = client.post("/api/v1/auth/login", json={"username": "tenant_b_user", "password": "password123"})
    assert login_b_res.status_code == 200
    token_b = login_b_res.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Tenant B tries to claim -> must fail with 409 Conflict
    second_claim_res = client.post(f"/api/v1/cases/{new_pending_case_id}/claim", headers=headers_b)
    print(f"   -> Tenant B claim attempt status code: {second_claim_res.status_code} (Conflict)")
    assert second_claim_res.status_code == 409
    assert "Case has already been claimed" in second_claim_res.json()["detail"]

    # Tenant B listing cases -> must NOT see this case anymore
    b_cases_res = client.get("/api/v1/cases", headers=headers_b)
    b_case_ids = [c["id"] for c in b_cases_res.json()["items"]]
    assert new_pending_case_id not in b_case_ids, "Case is now active under Tenant A and must not leak to Tenant B!"
    print("   -> Tenant B cannot view Tenant A's newly claimed active case.")
    print("   -> Scenario 3 PASSED: Cross-tenant claim succeeded, isolated from Tenant B.")

    print("\n" + "=" * 70)
    print("ALL 3 REQUIRED SCENARIOS VALIDATED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_scenarios()
