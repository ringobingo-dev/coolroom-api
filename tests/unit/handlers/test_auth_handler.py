import json
import jwt
from datetime import datetime, timedelta
from src.handlers.auth_handler import generate_token, handler, JWT_SECRET

class MockContext:
    """Mock Lambda context for testing."""
    def __init__(self):
        self.function_name = "test-function"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "test:arn"
        self.aws_request_id = "test-id"

# Create mock context
mock_context = MockContext()

def test_generate_token():
    """Test token generation."""
    username = "testuser"
    token = generate_token(username)
    decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    assert decoded['sub'] == username
    assert 'exp' in decoded

def test_debug():
    """Test debug endpoint."""
    event = {
        "headers": {
            "Content-Type": "application/json"
        },
        "httpMethod": "GET",
        "path": "/debug",
        "requestContext": {
            "httpMethod": "GET",
            "path": "/debug"
        }
    }
    
    response = handler(event, mock_context)
    body = json.loads(response['body'])
    assert response['statusCode'] == 200
    assert body['message'] == "Debug endpoint working"

def test_login_success():
    """Test successful login request."""
    event = {
        "body": json.dumps({"username": "testuser", "password": "testpass"}),
        "headers": {
            "Content-Type": "application/json"
        },
        "httpMethod": "POST",
        "path": "/login",
        "requestContext": {
            "httpMethod": "POST",
            "path": "/login"
        }
    }
    
    response = handler(event, mock_context)
    body = json.loads(response['body'])
    assert response['statusCode'] == 200
    assert 'token' in body
    assert 'message' in body
    assert body['message'] == "Login successful"

def test_login_missing_credentials():
    """Test login request with missing credentials."""
    event = {
        "body": json.dumps({"username": ""}),
        "headers": {
            "Content-Type": "application/json"
        },
        "httpMethod": "POST",
        "path": "/login",
        "requestContext": {
            "httpMethod": "POST",
            "path": "/login"
        }
    }
    
    response = handler(event, mock_context)
    body = json.loads(response['body'])
    assert response['statusCode'] == 400
    assert 'message' in body
    assert body['message'] == "Username and password are required"

def test_token_expiry():
    """Test that generated tokens have correct expiry time."""
    username = "testuser"
    token = generate_token(username)
    decoded = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
    
    # Get expiry time from token
    exp_time = datetime.fromtimestamp(decoded['exp'])
    iat_time = datetime.fromtimestamp(decoded['iat'])
    
    # Check expiry is set correctly (between now and 24 hours from issue time)
    assert exp_time > iat_time
    assert exp_time <= iat_time + timedelta(hours=24)  # Default expiry

def test_login_missing_password():
    """Test login request with missing password."""
    event = {
        "body": json.dumps({"username": "testuser"}),
        "headers": {
            "Content-Type": "application/json"
        },
        "httpMethod": "POST",
        "path": "/login",
        "requestContext": {
            "httpMethod": "POST",
            "path": "/login"
        }
    }
    
    response = handler(event, mock_context)
    body = json.loads(response['body'])
    assert response['statusCode'] == 400
    assert body['message'] == "Username and password are required"

def test_login_invalid_json():
    """Test login request with invalid JSON body."""
    event = {
        "body": "invalid json",
        "headers": {
            "Content-Type": "application/json"
        },
        "httpMethod": "POST",
        "path": "/login",
        "requestContext": {
            "httpMethod": "POST",
            "path": "/login"
        }
    }
    
    response = handler(event, mock_context)
    body = json.loads(response['body'])
    assert response['statusCode'] == 500
    assert 'message' in body
    assert body['message'] == "Internal server error"

def test_login_empty_body():
    """Test login request with empty body."""
    event = {
        "body": None,
        "headers": {
            "Content-Type": "application/json"
        },
        "httpMethod": "POST",
        "path": "/login",
        "requestContext": {
            "httpMethod": "POST",
            "path": "/login"
        }
    }
    
    response = handler(event, mock_context)
    body = json.loads(response['body'])
    assert response['statusCode'] == 500
    assert 'message' in body

def test_login_missing_body():
    """Test login request with missing body."""
    event = {
        "headers": {
            "Content-Type": "application/json"
        },
        "httpMethod": "POST",
        "path": "/login",
        "requestContext": {
            "httpMethod": "POST",
            "path": "/login"
        }
    }
    
    response = handler(event, mock_context)
    body = json.loads(response['body'])
    assert response['statusCode'] == 500
    assert 'message' in body