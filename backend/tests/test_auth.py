def test_successful_login(client, seed_test_data):
    """Test authenticating with valid credentials returns JWT token and user info."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "user_a", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "user_a"
    assert data["user"]["tenant_id"] == "tenant-a-uuid"


def test_login_invalid_password(client, seed_test_data):
    """Test authenticating with incorrect password returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "user_a", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


def test_login_nonexistent_user(client, seed_test_data):
    """Test authenticating with unknown username returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent", "password": "password123"},
    )
    assert response.status_code == 401


def test_protected_endpoint_without_token(client):
    """Test accessing protected cases endpoint without Authorization header returns 401."""
    response = client.get("/api/v1/cases")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


def test_protected_endpoint_with_invalid_token(client):
    """Test accessing protected cases endpoint with forged or invalid token returns 401."""
    response = client.get(
        "/api/v1/cases",
        headers={"Authorization": "Bearer invalid_token_xyz"},
    )
    assert response.status_code == 401


def test_get_current_user_profile(client, auth_headers_a):
    """Test /auth/me returns current user details."""
    response = client.get("/api/v1/auth/me", headers=auth_headers_a)
    assert response.status_code == 200
    assert response.json()["username"] == "user_a"
