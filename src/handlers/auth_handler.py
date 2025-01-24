import os
import json
import jwt
from datetime import datetime, timedelta
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize utilities
logger = Logger(level="DEBUG")  # Set to DEBUG for more verbose logging
tracer = Tracer()
app = APIGatewayRestResolver()

# Log registered routes
logger.debug("Initializing routes...")

# Constants
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-here')
TOKEN_EXPIRY = int(os.environ.get('TOKEN_EXPIRY_HOURS', '24'))

@app.post("/login")
@tracer.capture_method
def login():
    """Handle login requests and generate JWT tokens."""
    logger.debug("Received login request")
    logger.debug(f"Event: {app.current_event}")
    logger.debug(f"Event raw: {app.current_event._data}")
    
    # Check if body exists and is not empty
    if not app.current_event.body:
        logger.warning("Missing request body")
        return {
            "status": "error",
            "message": "Request body is required"
        }, 400

    # Try to parse JSON body
    try:
        body = json.loads(app.current_event.body)
        logger.debug(f"Request body: {body}")
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON in request body: {str(e)}")
        return {
            "status": "error",
            "message": "Invalid JSON format in request body"
        }, 400
    except Exception as e:
        logger.exception(f"Error processing request body: {str(e)}")
        return {
            "status": "error",
            "message": "Error processing request body"
        }, 400

    try:
        username = body.get('username')
        password = body.get('password')

        # Basic validation
        if not username or not password:
            logger.warning("Missing username or password")
            return {
                "status": "error",
                "message": "Username and password are required"
            }, 400

        # TODO: Replace with actual user authentication
        # For testing, accept any username/password combination
        logger.debug(f"Generating token for user: {username}")
        token = generate_token(username)
        return {
            "status": "success",
            "token": token,
            "message": "Login successful"
        }, 200

    except Exception as e:
        logger.exception(f"Login error: {str(e)}")
        return {
            "status": "error",
            "message": "Internal server error"
        }, 500

@app.get("/debug")
def debug():
    """Debug endpoint to verify routing."""
    logger.debug("Debug endpoint called")
    return {"message": "Debug endpoint working"}

def generate_token(username: str) -> str:
    """Generate a JWT token for the user."""
    try:
        expiry = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRY)
        payload = {
            'sub': username,
            'exp': expiry,
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
        logger.debug(f"Generated token successfully")
        return token
    except Exception as e:
        logger.exception(f"Token generation error: {str(e)}")
        raise

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> dict:
    """Main Lambda handler."""
    logger.debug(f"Received event: {json.dumps(event)}")
    logger.debug(f"Event type: {type(event)}")
    logger.debug(f"Event keys: {event.keys()}")
    logger.debug(f"Current path: {event.get('path')}")
    logger.debug(f"Current method: {event.get('httpMethod')}")
    
    # Debug route matching
    path = event.get('path', '')
    if not path.startswith('/'):
        path = f"/{path}"
        event['path'] = path
    method = event.get('httpMethod', '')
    logger.debug(f"Attempting to match route: {method} {path}")
    
    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception(f"Error resolving event: {str(e)}")
        return {
            "status": "error",
            "message": "Internal server error"
        }, 500