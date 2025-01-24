import os
import json
import jwt
from datetime import datetime, timedelta
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize utilities
logger = Logger()
tracer = Tracer()
app = APIGatewayRestResolver()

# Constants
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')
TOKEN_EXPIRY = int(os.environ.get('TOKEN_EXPIRY_HOURS', '24'))

@app.post("/auth/login")
@tracer.capture_method
def login():
    """Handle login requests and generate JWT tokens."""
    try:
        body = app.current_event.json_body
        username = body.get('username')
        password = body.get('password')

        # Basic validation
        if not username or not password:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": "Username and password are required"
                })
            }

        # TODO: Replace with actual user authentication
        # For testing, accept any username/password combination
        if username and password:
            token = generate_token(username)
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "token": token,
                    "message": "Login successful"
                })
            }

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Internal server error"
            })
        }

def generate_token(username: str) -> str:
    """Generate a JWT token for the user."""
    try:
        expiry = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY)
        payload = {
            'sub': username,
            'exp': expiry,
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        raise

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> dict:
    """Main Lambda handler."""
    return app.resolve(event, context)