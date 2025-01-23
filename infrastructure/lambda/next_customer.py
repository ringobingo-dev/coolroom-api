import json
import os
import uuid
import boto3
from datetime import datetime
from botocore.exceptions import ClientError

def handler(event, context):
    """Main handler for customer operations"""
    method = event['httpMethod']
    
    if method == 'POST':
        return create_next_customer(event, context)
    elif method == 'GET':
        return get_customer(event, context)
    elif method == 'PUT':
        return update_customer(event, context)
    else:
        return {
            'statusCode': 405,
            'body': json.dumps({
                'error': 'Method not allowed'
            })
        }

def create_next_customer(event, context):
    """Creates next customer with validation"""
    try:
        body = json.loads(event['body'])
        
        # Validate required fields
        required_fields = ['name', 'email', 'customer_type', 'business_details']
        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': f"Missing required fields: {', '.join(missing_fields)}"
                })
            }
        
        # Initialize DynamoDB
        dynamodb = boto3.resource('dynamodb')
        customer_table = dynamodb.Table(os.environ['CUSTOMER_TABLE'])
        
        # Create customer item
        timestamp = datetime.utcnow().isoformat()
        customer_id = str(uuid.uuid4())
        
        customer_item = {
            'customer_id': customer_id,
            'name': body['name'],
            'email': body['email'],
            'customer_type': body['customer_type'],
            'status': 'ACTIVE',
            'created_at': timestamp,
            'updated_at': timestamp,
            'business_details': body['business_details']
        }
        
        # Save to DynamoDB
        customer_table.put_item(Item=customer_item)
        
        return {
            'statusCode': 201,
            'body': json.dumps({
                'message': 'Customer created successfully',
                'customer': customer_item
            })
        }
        
    except Exception as e:
        print(f"Error creating customer: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        }
