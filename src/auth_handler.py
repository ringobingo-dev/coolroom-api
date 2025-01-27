import json
from datetime import datetime, timedelta
import jwt
import bcrypt
import os

# Environment Variables
JWT_SECRET = os.getenv('JWT_SECRET', 'your_jwt_secret')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# In-memory user store for testing purposes (replace with database)
users_db = {}

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_jwt_token(user_data: dict) -> str:
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {**user_data, "exp": expiration}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def register_user(body: dict):
    email = body.get("email")
    password = body.get("password")

    if email in users_db:
        return {
            "statusCode": 409,
            "body": json.dumps({"message": "User already exists"})
        }

    hashed_password = hash_password(password)
    users_db[email] = {
        "email": email,
        "password": hashed_password,
        "first_name": "John",
        "last_name": "Doe",
        "role": "user",
        "created_at": datetime.utcnow()
    }

    user_data = users_db[email]
    return {
        "statusCode": 201,
        "body": json.dumps({
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "role": user_data["role"]
        })
    }

def login_user(body: dict):
    email = body.get("email")
    password = body.get("password")

    user_data = users_db.get(email)
    if not user_data or not verify_password(password, user_data["password"]):
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Invalid credentials"})
        }

    token = create_jwt_token({"email": email, "role": user_data["role"]})
    return {
        "statusCode": 200,
        "body": json.dumps({"token": token})
    }

def get_user_profile(headers: dict):
    token = headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload["email"]

        user_data = users_db.get(email)
        if not user_data:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "User not found"})
            }

        return {
            "statusCode": 200,
            "body": json.dumps({
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "role": user_data["role"]
            })
        }
    except jwt.ExpiredSignatureError:
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Token has expired"})
        }
    except jwt.InvalidTokenError:
        return {
            "statusCode": 401,
            "body": json.dumps({"message": "Invalid token"})
        }

def lambda_handler(event, context):
    try:
        http_method = event.get("httpMethod")
        path = event.get("path")
        body = json.loads(event.get("body", "{}"))
        headers = event.get("headers", {})

        if path == "/auth/register" and http_method == "POST":
            return register_user(body)
        elif path == "/auth/login" and http_method == "POST":
            return login_user(body)
        elif path == "/auth/profile" and http_method == "GET":
            return get_user_profile(headers)
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "Not found"})
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Internal server error: {str(e)}"})
        }

