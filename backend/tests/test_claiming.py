def test_valid_cross_tenant_claim(client, seed_test_data, auth_headers_a, db_session):
    """Test Scenario 3: Cross-tenant claim.
    A pending case originated by Tenant B is claimed by Tenant A staff user.
    Expected:
    - Status transitions to 'active'
    - Case tenant_id is set to Tenant A
    - assigned_user_id is set to user_a
    - claimed_at is populated
    """
    pending_case_id = seed_test_data["case_pending"].id
    
    response = client.post(
        f"/api/v1/cases/{pending_case_id}/claim",
        headers=auth_headers_a,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == pending_case_id
    assert data["status"] == "active"
    assert data["tenant_id"] == "tenant-a-uuid"
    assert data["assigned_user_id"] == "user-a-uuid"
    assert data["claimed_at"] is not None


def test_cannot_claim_already_active_case(client, seed_test_data, auth_headers_b):
    """Attempting to claim an already active case must fail with HTTP 409 Conflict."""
    active_case_id = seed_test_data["case_a_active"].id
    response = client.post(
        f"/api/v1/cases/{active_case_id}/claim",
        headers=auth_headers_b,
    )
    assert response.status_code == 409
    assert "Case has already been claimed" in response.json()["detail"]


def test_cannot_claim_closed_case(client, seed_test_data, auth_headers_a):
    """Attempting to claim a closed case must fail with HTTP 409 Conflict."""
    closed_case_id = seed_test_data["case_b_closed"].id
    response = client.post(
        f"/api/v1/cases/{closed_case_id}/claim",
        headers=auth_headers_a,
    )
    assert response.status_code == 409
    assert "Case has already been claimed" in response.json()["detail"]


def test_concurrent_claim_race_condition(client, seed_test_data, auth_headers_a, auth_headers_b):
    """Simulate two users attempting to claim the same pending case:
    The first claim must succeed (HTTP 200).
    The subsequent claim must fail with HTTP 409 Conflict.
    """
    pending_case_id = seed_test_data["case_pending"].id
    
    # First claim by User A
    res1 = client.post(f"/api/v1/cases/{pending_case_id}/claim", headers=auth_headers_a)
    assert res1.status_code == 200
    assert res1.json()["status"] == "active"
    assert res1.json()["tenant_id"] == "tenant-a-uuid"

    # Second claim by User B
    res2 = client.post(f"/api/v1/cases/{pending_case_id}/claim", headers=auth_headers_b)
    assert res2.status_code == 409
    assert "Case has already been claimed" in res2.json()["detail"]
