import json
import os
import boto3
from datetime import datetime
from validation import validate_user_input

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('USER_TABLE_NAME'))

def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

def handler(event, context):
    try:
        http_method = event['httpMethod']
        
        # GET user
        if http_method == 'GET':
            customer_id = event['pathParameters']['customer_id']
            response = table.get_item(Key={'customer_id': customer_id})
            item = response.get('Item')
            
            if not item:
                return create_response(404, {'error': 'User not found'})
            return create_response(200, item)
            
        # POST new user
        elif http_method == 'POST':
            body = json.loads(event['body'])
            
            # Validate input
            is_valid, errors = validate_user_input(body)
            if not is_valid:
                return create_response(400, {'errors': errors})
            
            customer_id = body['customer_id']
            
            # Check if user exists
            response = table.get_item(Key={'customer_id': customer_id})
            if response.get('Item'):
                return create_response(400, {'error': 'User already exists'})
            
            # Add timestamp
            body['created_at'] = datetime.utcnow().isoformat()
            
            # Create user
            table.put_item(Item=body)
            return create_response(201, body)
            
        # PUT update user
        elif http_method == 'PUT':
            customer_id = event['pathParameters']['customer_id']
            body = json.loads(event['body'])
            
            # Check if user exists
            response = table.get_item(Key={'customer_id': customer_id})
            if not response.get('Item'):
                return create_response(404, {'error': 'User not found'})
            
            # Update timestamp
            body['updated_at'] = datetime.utcnow().isoformat()
            
            # Update user
            update_expression = 'SET '
            expression_values = {}
            
            for key, value in body.items():
                if key != 'customer_id':  # Don't update the primary key
                    update_expression += f'#{key} = :{key}, '
                    expression_values[f':{key}'] = value
            
            update_expression = update_expression.rstrip(', ')
            
            table.update_item(
                Key={'customer_id': customer_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames={f'#{k}': k for k in body.keys() if k != 'customer_id'}
            )
            
            return create_response(200, {'message': 'User updated successfully'})
            
        # DELETE user
        elif http_method == 'DELETE':
            customer_id = event['pathParameters']['customer_id']
            
            # Check if user exists
            response = table.get_item(Key={'customer_id': customer_id})
            if not response.get('Item'):
                return create_response(404, {'error': 'User not found'})
            
            # Delete user
            table.delete_item(Key={'customer_id': customer_id})
            return create_response(200, {'message': 'User deleted successfully'})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})
