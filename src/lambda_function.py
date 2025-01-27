import os
import json
import jwt
import bcrypt
import boto3
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
user_table = dynamodb.Table(os.environ.get('USER_TABLE'))
test_case_table = dynamodb.Table(os.environ.get('TEST_CASE_TABLE'))

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
        email = body['email']
        password = body['password']
        first_name = body['firstName']
        last_name = body['lastName']
        role = body.get('role', 'user')

        response = user_table.get_item(Key={'email': email})
        if 'Item' in response:
            return {
                'statusCode': 409,
                'body': json.dumps({'message': 'User with this email already exists'})
            }

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
        user_response = {k: v for k, v in user.items() if k != 'password'}

        return {
            'statusCode': 201,
            'body': json.dumps(user_response)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Internal server error: {str(e)}'})
        }

def login_user(body):
    """Authenticate a user and return a token"""
    try:
        email = body['email']
        password = body['password']

        response = user_table.get_item(Key={'email': email})
        if 'Item' not in response:
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Invalid credentials'})
            }

        user = response['Item']
        if not verify_password(password, user['password'].encode('utf-8')):
            return {
                'statusCode': 401,
                'body': json.dumps({'message': 'Invalid credentials'})
            }

        token = create_token(user['email'], user['email'], user['role'])
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
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Internal server error: {str(e)}'})
        }

def manage_test_cases(event):
    """Handle warehouse test case operations"""
    try:
        http_method = event['httpMethod']
        path = event['path']
        body = json.loads(event['body']) if event.get('body') else {}

        if http_method == 'POST' and path == '/warehouse/test-cases':
            # Create a new test case
            test_case_id = body.get('id')
            name = body.get('name')
            description = body.get('description')
            timestamp = datetime.utcnow().isoformat()

            test_case = {
                'id': test_case_id,
                'name': name,
                'description': description,
                'status': 'pending',
                'createdAt': timestamp,
                'updatedAt': timestamp
            }

            test_case_table.put_item(Item=test_case)

            return {
                'statusCode': 201,
                'body': json.dumps(test_case)
            }

        elif http_method == 'GET' and path.startswith('/warehouse/test-cases'):
            # Retrieve test cases or a specific test case
            if 'id' in event['queryStringParameters']:
                test_case_id = event['queryStringParameters']['id']
                response = test_case_table.get_item(Key={'id': test_case_id})
                if 'Item' in response:
                    return {
                        'statusCode': 200,
                        'body': json.dumps(response['Item'])
                    }
                else:
                    return {
                        'statusCode': 404,
                        'body': json.dumps({'message': 'Test case not found'})
                    }
            else:
                response = test_case_table.scan()
                return {
                    'statusCode': 200,
                    'body': json.dumps(response['Items'])
                }

        return {
            'statusCode': 404,
            'body': json.dumps({'message': 'Not found'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Internal server error: {str(e)}'})
        }

def lambda_handler(event, context):
    """Main handler for the API"""
    try:
        http_method = event['httpMethod']
        path = event['path']

        if path.startswith('/auth/'):
            if path == '/auth/register':
                return register_user(json.loads(event['body']))
            elif path == '/auth/login':
                return login_user(json.loads(event['body']))

        elif path.startswith('/warehouse/'):
            return manage_test_cases(event)

        return {
            'statusCode': 404,
            'body': json.dumps({'message': 'Endpoint not found'})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'message': f'Internal server error: {str(e)}'})
        }

