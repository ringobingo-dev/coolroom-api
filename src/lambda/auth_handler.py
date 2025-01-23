import json
import os
import boto3
import jwt
import bcrypt
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
user_table = dynamodb.Table(os.environ.get('USER_TABLE'))

# JWT configuration
JWT_SECRET = os.environ.get('JWT_SECRET')
JWT_EXPIRATION = 24  # hours

def create_token(user_id, email, role):
    """Create a JWT token for the user"""
    exp_time = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION)
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': exp_time
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt)

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def register_user(body):
    """Register a new user"""
    try:
        # Extract user data
        email = body['email']
        password = body['password']
        first_name = body['firstName']
        last_name = body['lastName']
        role = body.get('role', 'user')  # Default role is 'user'

        # Check if user exists
        response = user_table.get_item(
            Key={'email': email}
        )
        if 'Item' in response:
            return {
                'statusCode': 409,
                'body': json.dumps({'message': 'User with this email already exists'})
            }

        # Hash password and create user
        hashed_password = hash_password(password)
        timestamp = datetime.utcnow().isoformat()
        
        user = {
            'email': email,
            'password': hashed_password.decode('utf-8'),
            'firstName': first_name,
            'lastName': last_name,
            'role': role,
            'createdAt': timestamp,
            'updatedAt': timestamp
        }
        
        user_table.put_item(Item=user)
        
        # Create response without password
        user_response = {k: v for k, v in user.items() if k != 'password'}
        
        return {
            'statusCode': 201,
            'body': json.dumps(user_response)
        }
        
    except Exception as e:
        print(f"Error in register_user: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }

def login_user(body):
    """Authenticate a user and return a token"""
    try:
        email = body['email']
        password = body['password']
        
        # Get user from database
        response = user_table.get_item(
            Key={'email': email}
        )
        
        if 'Item' not in response:
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Invalid credentials'})
            }
            
        user = response['Item']
        
        # Verify password
        if not verify_password(password, user['password'].encode('utf-8')):
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Invalid credentials'})
            }
            
        # Generate token
        token = create_token(user['email'], user['email'], user['role'])
        
        # Create response
        user_response = {
            'token': token,
            'user': {
                'email': user['email'],
                'firstName': user['firstName'],
                'lastName': user['lastName'],
                'role': user['role']
            }
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(user_response)
        }
        
    except Exception as e:
        print(f"Error in login_user: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }

def get_user_profile(event):
    """Get the profile of the authenticated user"""
    try:
        # Get token from Authorization header
        auth_header = event['headers'].get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Missing or invalid token'})
            }
            
        token = auth_header.split(' ')[1]
        
        try:
            # Verify and decode token
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            email = payload['email']
            
            # Get user from database
            response = user_table.get_item(
                Key={'email': email}
            )
            
            if 'Item' not in response:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'message': 'User not found'})
                }
                
            user = response['Item']
            
            # Create response without password
            user_response = {k: v for k, v in user.items() if k != 'password'}
            
            return {
                'statusCode': 200,
                'body': json.dumps(user_response)
            }
            
        except jwt.ExpiredSignatureError:
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Token has expired'})
            }
        except jwt.InvalidTokenError:
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Invalid token'})
            }
            
    except Exception as e:
        print(f"Error in get_user_profile: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }

def lambda_handler(event, context):
    """Main handler for authentication endpoints"""
    try:
        http_method = event['httpMethod']
        path = event['path']
        
        # Parse request body if present
        body = {}
        if event.get('body'):
            body = json.loads(event['body'])
            
        # Route to appropriate handler
        if path == '/auth/register' and http_method == 'POST':
            return register_user(body)
        elif path == '/auth/login' and http_method == 'POST':
            return login_user(body)
        elif path == '/auth/profile' and http_method == 'GET':
            return get_user_profile(event)
        else:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Not found'})
            }
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        } 