import os
import pytest

@pytest.fixture(autouse=True)
def env_setup():
    """Set up test environment variables."""
    os.environ['JWT_SECRET'] = 'test-secret-key'
    os.environ['TOKEN_EXPIRY_HOURS'] = '24'
    
@pytest.fixture
def mock_event():
    """Create a mock API Gateway event."""
    return {
        "body": '{"username": "testuser", "password": "testpass"}',
        "httpMethod": "POST",
        "path": "/login",
        "requestContext": {
            "httpMethod": "POST",
            "path": "/login"
        }
    }