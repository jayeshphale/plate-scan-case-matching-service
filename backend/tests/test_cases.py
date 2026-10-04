def test_get_case_scans_authorized(client, seed_test_data, auth_headers_a):
    """Tenant A can retrieve location trail for Tenant A's active case."""
    case_a_id = seed_test_data["case_a_active"].id
    response = client.get(f"/api/v1/cases/{case_a_id}/scans", headers=auth_headers_a)
    assert response.status_code == 200
    scans = response.json()
    assert len(scans) == 2
    # Verify chronological ordering (scanned_at ASC)
    assert scans[0]["scanned_at"] <= scans[1]["scanned_at"]
    assert scans[0]["vin"] == "1FTFW1E51NFA12345"


def test_get_case_scans_unauthorized_forbidden(client, seed_test_data, auth_headers_b):
    """Tenant B cannot access scans for Tenant A's active case (HTTP 403)."""
    case_a_id = seed_test_data["case_a_active"].id
    response = client.get(f"/api/v1/cases/{case_a_id}/scans", headers=auth_headers_b)
    assert response.status_code == 403
    assert "You do not have access to this case" in response.json()["detail"]


def test_get_case_scans_pending_case_accessible(client, seed_test_data, auth_headers_a):
    """Any tenant can view scans for a pending_claim case."""
    pending_case_id = seed_test_data["case_pending"].id
    response = client.get(f"/api/v1/cases/{pending_case_id}/scans", headers=auth_headers_a)
    assert response.status_code == 200


def test_filter_cases_by_vin(client, seed_test_data, auth_headers_a):
    """Filter cases by VIN returns only matching case."""
    response = client.get(
        "/api/v1/cases?vin=1FTFW1E51NFA12345",
        headers=auth_headers_a,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["vin"] == "1FTFW1E51NFA12345"


def test_mock_partner_eligibility_endpoint(client):
    """Test POST /mock/partner-network/eligibility returns true for configured VIN."""
    response = client.post(
        "/mock/partner-network/eligibility",
        json={"vin": "5NPE34AF9KH123456"},
    )
    assert response.status_code == 200
    assert response.json()["still_eligible_for_repo"] is True
