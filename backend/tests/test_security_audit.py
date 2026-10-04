import pytest
from datetime import datetime, timezone, timedelta
from jose import jwt
from app.core.config import settings
from app.models.tenant import Tenant
from app.models.user import User
from app.models.camera import Camera
from app.models.case import Case
from app.models.scan import Scan
from app.core.security import get_password_hash, create_access_token


class TestMultiTenantSecurityAudit:
    """Rigorous security audit verifying tenant boundaries and the deliberate pending claim exception."""

    def test_tenant_a_cannot_access_tenant_b_active_case(self, client, seed_test_data, auth_headers_a, db_session):
        """Tenant A must receive 403 Forbidden when requesting Tenant B's active case."""
        # Create an active case for Tenant B
        case_b_active = Case(
            id="case-b-active-uuid",
            vin="VIN_B_ACTIVE_999",
            origin_tenant_id=seed_test_data["tenant_b"].id,
            tenant_id=seed_test_data["tenant_b"].id,
            assigned_user_id=seed_test_data["user_b"].id,
            status="active",
        )
        db_session.add(case_b_active)
        db_session.commit()

        # Tenant A tries to read Tenant B's active case
        response = client.get(f"/api/v1/cases/{case_b_active.id}", headers=auth_headers_a)
        assert response.status_code == 403
        assert "You do not have access to this case" in response.json()["detail"]

    def test_tenant_a_cannot_access_tenant_b_closed_case(self, client, seed_test_data, auth_headers_a):
        """Tenant A must receive 403 Forbidden when requesting Tenant B's closed case."""
        closed_case_b = seed_test_data["case_b_closed"].id
        response = client.get(f"/api/v1/cases/{closed_case_b}", headers=auth_headers_a)
        assert response.status_code == 403
        assert "You do not have access to this case" in response.json()["detail"]

    def test_tenant_a_cannot_access_tenant_b_active_scans(self, client, seed_test_data, auth_headers_a, db_session):
        """Tenant A must receive 403 Forbidden when requesting scan trail for Tenant B's active case."""
        case_b_active = Case(
            id="case-b-active-scans-uuid",
            vin="VIN_B_ACTIVE_SCANS",
            origin_tenant_id=seed_test_data["tenant_b"].id,
            tenant_id=seed_test_data["tenant_b"].id,
            assigned_user_id=seed_test_data["user_b"].id,
            status="active",
        )
        db_session.add(case_b_active)
        db_session.commit()

        response = client.get(f"/api/v1/cases/{case_b_active.id}/scans", headers=auth_headers_a)
        assert response.status_code == 403
        assert "You do not have access to this case" in response.json()["detail"]

    def test_case_listing_strict_isolation_matrix(self, client, seed_test_data, auth_headers_a, auth_headers_b, db_session):
        """Verify complete case listing isolation matrix:
        Tenant A sees: Tenant A active cases, Tenant A closed cases, ALL pending cases.
        Tenant A MUST NOT see: Tenant B active cases, Tenant B closed cases.
        Same rule applies in reverse for Tenant B.
        """
        # Create a closed case for Tenant A
        case_a_closed = Case(
            id="case-a-closed-uuid",
            vin="VIN_A_CLOSED_111",
            origin_tenant_id=seed_test_data["tenant_a"].id,
            tenant_id=seed_test_data["tenant_a"].id,
            status="closed",
        )
        db_session.add(case_a_closed)
        db_session.commit()

        # 1. Query as Tenant A
        res_a = client.get("/api/v1/cases", headers=auth_headers_a)
        assert res_a.status_code == 200
        items_a = res_a.json()["items"]
        ids_a = [item["id"] for item in items_a]

        assert seed_test_data["case_a_active"].id in ids_a
        assert case_a_closed.id in ids_a
        assert seed_test_data["case_pending"].id in ids_a
        assert seed_test_data["case_b_closed"].id not in ids_a

        # 2. Query as Tenant B
        res_b = client.get("/api/v1/cases", headers=auth_headers_b)
        assert res_b.status_code == 200
        items_b = res_b.json()["items"]
        ids_b = [item["id"] for item in items_b]

        assert seed_test_data["case_b_closed"].id in ids_b
        assert seed_test_data["case_pending"].id in ids_b
        assert seed_test_data["case_a_active"].id not in ids_b
        assert case_a_closed.id not in ids_b


class TestPendingClaimExceptionAndLifecycle:
    """Verify the deliberate pending_claim exception, cross-tenant claiming, and subsequent isolation."""

    def test_pending_case_lifecycle_and_isolation_transition(self, client, seed_test_data, auth_headers_a, auth_headers_b, db_session):
        """1. Tenant A views Tenant B's pending case and its location trail.
        2. Tenant A claims it -> status='active', tenant_id=Tenant A, assigned_user=Tenant A user.
        3. Tenant B is immediately blocked from claiming or viewing the case.
        """
        pending_id = seed_test_data["case_pending"].id

        # 1. Tenant A can view pending case and scans
        res_view = client.get(f"/api/v1/cases/{pending_id}", headers=auth_headers_a)
        assert res_view.status_code == 200
        assert res_view.json()["status"] == "pending_claim"

        res_scans = client.get(f"/api/v1/cases/{pending_id}/scans", headers=auth_headers_a)
        assert res_scans.status_code == 200

        # 2. Tenant A claims the case
        res_claim = client.post(f"/api/v1/cases/{pending_id}/claim", headers=auth_headers_a)
        assert res_claim.status_code == 200
        claimed_data = res_claim.json()
        assert claimed_data["status"] == "active"
        assert claimed_data["tenant_id"] == "tenant-a-uuid"
        assert claimed_data["assigned_user_id"] == "user-a-uuid"
        assert claimed_data["claimed_at"] is not None

        # 3. Tenant B can NO LONGER see it under pending_claim filter
        res_b_pending = client.get("/api/v1/cases?status=pending_claim", headers=auth_headers_b)
        assert res_b_pending.status_code == 200
        b_pending_ids = [c["id"] for c in res_b_pending.json()["items"]]
        assert pending_id not in b_pending_ids

        # 4. Tenant B cannot see it in general listing
        res_b_all = client.get("/api/v1/cases", headers=auth_headers_b)
        b_all_ids = [c["id"] for c in res_b_all.json()["items"]]
        assert pending_id not in b_all_ids

        # 5. Tenant B direct detail request is rejected with 403 Forbidden
        res_b_direct = client.get(f"/api/v1/cases/{pending_id}", headers=auth_headers_b)
        assert res_b_direct.status_code == 403

        # 6. Tenant B direct scans request is rejected with 403 Forbidden
        res_b_scans = client.get(f"/api/v1/cases/{pending_id}/scans", headers=auth_headers_b)
        assert res_b_scans.status_code == 403

        # 7. Tenant B claim attempt is rejected with 409 Conflict
        res_b_claim = client.post(f"/api/v1/cases/{pending_id}/claim", headers=auth_headers_b)
        assert res_b_claim.status_code == 409
        assert "Case has already been claimed" in res_b_claim.json()["detail"]


class TestScanIngestionSecurityAndAuthority:
    """Verify camera webhook authority, tenant resolution, and data retention."""

    def test_tenant_id_in_scan_payload_is_ignored(self, client, seed_test_data, db_session):
        """Malicious payload specifying a spoofed tenant_id must be completely ignored.
        Tenant attribution must come EXCLUSIVELY from the resolved camera_id.
        """
        payload = {
            "camera_id": "cam_1001",  # Belongs to Tenant A
            "tenant_id": "tenant-b-uuid",  # Attempting to forge Tenant B
            "plate": "SPOOF1",
            "vin": "VIN_SPOOF_CHECK",
            "latitude": 33.7490,
            "longitude": -84.3880,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }
        response = client.post("/api/v1/scans", json=payload)
        assert response.status_code == 201
        data = response.json()
        # MUST resolve to Tenant A, NOT Tenant B
        assert data["tenant_id"] == "tenant-a-uuid"

    def test_unknown_camera_rejected(self, client):
        """Unknown camera_id must be rejected with 404."""
        payload = {
            "camera_id": "cam_nonexistent_9999",
            "plate": "TEST",
            "vin": "VIN_UNKNOWN",
            "latitude": 33.0,
            "longitude": -84.0,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }
        res = client.post("/api/v1/scans", json=payload)
        assert res.status_code == 404

    def test_inactive_camera_rejected(self, client, seed_test_data):
        """Deactivated camera must be rejected with 400."""
        payload = {
            "camera_id": "cam_disabled",
            "plate": "TEST",
            "vin": "VIN_DISABLED",
            "latitude": 33.0,
            "longitude": -84.0,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }
        res = client.post("/api/v1/scans", json=payload)
        assert res.status_code == 400

    def test_ineligible_vehicle_scan_stored_in_database_without_case(self, client, db_session, seed_test_data):
        """Ineligible vehicle scan must be stored in DB, but NO case must be created."""
        initial_scans = db_session.query(Scan).count()
        initial_cases = db_session.query(Case).count()
        ineligible_vin = "INELIGIBLE_CAR_99999"

        payload = {
            "camera_id": "cam_1001",
            "plate": "INELG1",
            "vin": ineligible_vin,
            "latitude": 33.7490,
            "longitude": -84.3880,
            "scanned_at": datetime.now(timezone.utc).isoformat(),
        }
        res = client.post("/api/v1/scans", json=payload)
        assert res.status_code == 201
        assert res.json()["created_new_case"] is False
        assert res.json()["case_id"] is None

        # Verify directly in DB
        assert db_session.query(Scan).count() == initial_scans + 1
        assert db_session.query(Case).count() == initial_cases
        stored = db_session.query(Scan).filter(Scan.vin == ineligible_vin).first()
        assert stored is not None
        assert stored.plate == "INELG1"

    def test_all_scans_stored_regardless_of_matching(self, client, db_session, seed_test_data):
        """Every scan (matched active, new eligible, ineligible) must remain in the scans table."""
        count_before = db_session.query(Scan).count()

        # Ingest 3 distinct scans
        scans_to_ingest = [
            {"camera_id": "cam_1001", "plate": "P1", "vin": "1FTFW1E51NFA12345", "latitude": 33.1, "longitude": -84.1, "scanned_at": datetime.now(timezone.utc).isoformat()},
            {"camera_id": "cam_2050", "plate": "P2", "vin": "5NPE34AF9KH123456", "latitude": 34.1, "longitude": -118.1, "scanned_at": datetime.now(timezone.utc).isoformat()},
            {"camera_id": "cam_1001", "plate": "P3", "vin": "INELIGIBLE_VIN_777", "latitude": 33.2, "longitude": -84.2, "scanned_at": datetime.now(timezone.utc).isoformat()},
        ]
        for p in scans_to_ingest:
            res = client.post("/api/v1/scans", json=p)
            assert res.status_code == 201

        count_after = db_session.query(Scan).count()
        assert count_after == count_before + 3


class TestAuthenticationSecurityAudit:
    """Verify password hashing, token validation, expired tokens, and inactive accounts."""

    def test_passwords_are_bcrypt_hashed(self, db_session, seed_test_data):
        """Passwords must NEVER be stored in plaintext."""
        user = db_session.query(User).filter(User.username == "user_a").first()
        assert user.password_hash != "password123"
        assert user.password_hash.startswith("$2")  # Standard bcrypt signature

    def test_expired_token_rejected_with_401(self, client, seed_test_data):
        """Expired JWT tokens must be rejected with 401."""
        now = datetime.now(timezone.utc)
        expired_payload = {
            "sub": seed_test_data["user_a"].id,
            "tenant_id": seed_test_data["tenant_a"].id,
            "role": "staff",
            "exp": now - timedelta(hours=1),
            "iat": now - timedelta(hours=2),
        }
        expired_token = jwt.encode(expired_payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        response = client.get("/api/v1/cases", headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401

    def test_forged_secret_token_rejected_with_401(self, client, seed_test_data):
        """Tokens signed with wrong secret key must be rejected with 401."""
        forged_payload = {
            "sub": seed_test_data["user_a"].id,
            "tenant_id": seed_test_data["tenant_a"].id,
            "role": "staff",
        }
        forged_token = jwt.encode(forged_payload, "wrong_secret_key_attacker", algorithm="HS256")
        response = client.get("/api/v1/cases", headers={"Authorization": f"Bearer {forged_token}"})
        assert response.status_code == 401

    def test_inactive_user_cannot_access_api(self, client, seed_test_data, db_session):
        """Inactive user account must be rejected with 401 even with a valid signature."""
        user = seed_test_data["user_a"]
        user.is_active = False
        db_session.commit()

        token = create_access_token({"sub": user.id, "tenant_id": user.tenant_id, "role": user.role})
        response = client.get("/api/v1/cases", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()


class TestSystemHealthAndMockPartner:
    """Verify health checks and partner network endpoints."""

    def test_health_check_returns_database_connected(self, client):
        """Health check must verify database connectivity."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["database"] == "ok"

    def test_mock_partner_eligibility_contract(self, client):
        """POST /mock/partner-network/eligibility contract test."""
        # 1. Configured eligible VIN
        res_eligible = client.post("/mock/partner-network/eligibility", json={"vin": "5NPE34AF9KH123456"})
        assert res_eligible.status_code == 200
        assert res_eligible.json()["still_eligible_for_repo"] is True

        # 2. Ineligible VIN
        res_ineligible = client.post("/mock/partner-network/eligibility", json={"vin": "UNKNOWN_RANDOM_VIN"})
        assert res_ineligible.status_code == 200
        assert res_ineligible.json()["still_eligible_for_repo"] is False
