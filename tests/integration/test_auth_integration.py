import json
import jwt
import pytest
import requests
from datetime import datetime, timedelta
from src.handlers.auth_handler import JWT_SECRET

# Test configuration
API_URL = "http://localhost:3000"  # Update this with your actual API endpoint

@pytest.fixture
def auth_headers():
    """Fixture for common headers used in requests."""
    return {
        "Content-Type": "application/json"
    }

def test_debug_endpoint_integration(auth_headers):
    """Integration test for debug endpoint."""
    response = requests.get(f"{API_URL}/debug", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Debug endpoint working"

def test_login_flow_integration(auth_headers):
    """Integration test for complete login flow."""
    # Test successful login
    login_data = {
        "username": "testuser",
        "password": "testpass"
    }
    response = requests.post(
        f"{API_URL}/login",
        headers=auth_headers,
        json=login_data
    )
    assert response.status_code == 200
    data = response.json()
    assert "token" in data
    assert "message" in data
    assert data["message"] == "Login successful"

    # Verify token is valid
    token = data["token"]
    decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    assert decoded["sub"] == login_data["username"]
    
    # Verify token expiry
    exp_time = datetime.fromtimestamp(decoded['exp'])
    iat_time = datetime.fromtimestamp(decoded['iat'])
    assert exp_time > iat_time
    assert exp_time <= iat_time + timedelta(hours=24)

def test_login_failures_integration(auth_headers):
    """Integration test for login failure scenarios."""
    # Test missing password
    response = requests.post(
        f"{API_URL}/login",
        headers=auth_headers,
        json={"username": "testuser"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == "Username and password are required"

    # Test missing username
    response = requests.post(
        f"{API_URL}/login",
        headers=auth_headers,
        json={"password": "testpass"}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == "Username and password are required"

    # Test empty credentials
    response = requests.post(
        f"{API_URL}/login",
        headers=auth_headers,
        json={"username": "", "password": ""}
    )
    assert response.status_code == 400
    data = response.json()
    assert data["message"] == "Username and password are required"

def test_invalid_requests_integration(auth_headers):
    """Integration test for invalid request handling."""
    # Test invalid JSON
    response = requests.post(
        f"{API_URL}/login",
        headers=auth_headers,
        data="invalid json"
    )
    assert response.status_code == 500
    data = response.json()
    assert "message" in data

    # Test missing body
    response = requests.post(
        f"{API_URL}/login",
        headers=auth_headers
    )
    assert response.status_code == 500
    data = response.json()
    assert "message" in data

@pytest.mark.parametrize("invalid_path", [
    "/invalid",
    "/login/invalid",
    "/debug/invalid",
])
def test_invalid_endpoints_integration(auth_headers, invalid_path):
    """Integration test for invalid endpoint handling."""
    response = requests.get(f"{API_URL}{invalid_path}", headers=auth_headers)
    assert response.status_code == 404

def test_method_not_allowed_integration(auth_headers):
    """Integration test for method not allowed scenarios."""
    # Test GET on login endpoint
    response = requests.get(f"{API_URL}/login", headers=auth_headers)
    assert response.status_code == 405

    # Test POST on debug endpoint
    response = requests.post(f"{API_URL}/debug", headers=auth_headers)
    assert response.status_code == 405