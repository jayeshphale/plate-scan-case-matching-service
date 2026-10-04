def test_tenant_cannot_view_other_tenant_closed_case(client, seed_test_data, auth_headers_a):
    """Tenant A user cannot fetch Tenant B's closed case details (HTTP 403)."""
    closed_case_b = seed_test_data["case_b_closed"].id
    response = client.get(f"/api/v1/cases/{closed_case_b}", headers=auth_headers_a)
    assert response.status_code == 403
    assert "You do not have access to this case" in response.json()["detail"]


def test_tenant_cannot_view_other_tenant_active_case(client, seed_test_data, auth_headers_b):
    """Tenant B user cannot fetch Tenant A's active case details (HTTP 403)."""
    active_case_a = seed_test_data["case_a_active"].id
    response = client.get(f"/api/v1/cases/{active_case_a}", headers=auth_headers_b)
    assert response.status_code == 403
    assert "You do not have access to this case" in response.json()["detail"]


def test_tenant_can_view_pending_case_from_other_tenant(client, seed_test_data, auth_headers_a):
    """Tenant A CAN view pending_claim case originated from Tenant B."""
    pending_case = seed_test_data["case_pending"].id
    response = client.get(f"/api/v1/cases/{pending_case}", headers=auth_headers_a)
    assert response.status_code == 200
    assert response.json()["id"] == pending_case
    assert response.json()["status"] == "pending_claim"


def test_case_list_tenant_isolation(client, seed_test_data, auth_headers_a):
    """Tenant A's case listing must include:
    - Tenant A's active case
    - The pending_claim case
    Must NOT include:
    - Tenant B's closed case
    """
    response = client.get("/api/v1/cases", headers=auth_headers_a)
    assert response.status_code == 200
    data = response.json()
    returned_case_ids = [c["id"] for c in data["items"]]

    # Tenant A active case must be present
    assert seed_test_data["case_a_active"].id in returned_case_ids
    # Pending case from any tenant must be present
    assert seed_test_data["case_pending"].id in returned_case_ids
    # Tenant B's closed case MUST NOT be present
    assert seed_test_data["case_b_closed"].id not in returned_case_ids


def test_filter_pending_claims_only(client, seed_test_data, auth_headers_a):
    """Querying ?status=pending_claim returns only pending cases."""
    response = client.get("/api/v1/cases?status=pending_claim", headers=auth_headers_a)
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    for case in data["items"]:
        assert case["status"] == "pending_claim"
