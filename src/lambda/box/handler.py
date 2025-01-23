import json
import os
import boto3
from datetime import datetime
from validation import validate_box_input

dynamodb = boto3.resource('dynamodb')
box_table = dynamodb.Table(os.environ.get('BOX_TABLE_NAME'))
user_table = dynamodb.Table(os.environ.get('USER_TABLE_NAME'))

def create_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }

def check_user_exists(customer_id):
    response = user_table.get_item(Key={'customer_id': customer_id})
    return bool(response.get('Item'))

def handler(event, context):
    try:
        http_method = event['httpMethod']
        
        # GET box history
        if http_method == 'GET':
            customer_id = event['pathParameters']['customer_id']
            
            # Check if specific box requested
            if 'room_id#box_id' in event['pathParameters']:
                box_id = event['pathParameters']['room_id#box_id']
                response = box_table.get_item(
                    Key={
                        'customer_id': customer_id,
                        'room_id#box_id': box_id
                    }
                )
                item = response.get('Item')
                
                if not item:
                    return create_response(404, {'error': 'Box not found'})
                return create_response(200, item)
            
            # List all boxes for customer
            else:
                response = box_table.query(
                    KeyConditionExpression='customer_id = :cid',
                    ExpressionAttributeValues={':cid': customer_id}
                )
                return create_response(200, response['Items'])
        
        # POST new box entry
        elif http_method == 'POST':
            body = json.loads(event['body'])
            
            # Validate input
            is_valid, errors = validate_box_input(body)
            if not is_valid:
                return create_response(400, {'errors': errors})
            
            # Check if user exists
            if not check_user_exists(body['customer_id']):
                return create_response(400, {'error': 'Customer does not exist'})
            
            # Add timestamps and history
            timestamp = datetime.utcnow().isoformat()
            body['created_at'] = timestamp
            body['updated_at'] = timestamp
            body['history'] = [{
                'action': body['action'],
                'timestamp': timestamp,
                'weight': body.get('weight'),
                'notes': body.get('notes')
            }]
            
            # Create box entry
            box_table.put_item(Item=body)
            return create_response(201, body)
            
        # PUT update box
        elif http_method == 'PUT':
            customer_id = event['pathParameters']['customer_id']
            box_id = event['pathParameters']['room_id#box_id']
            body = json.loads(event['body'])
            
            # Validate action
            if not validate_action(body.get('action', '')):
                return create_response(400, {'error': 'Invalid action'})
            
            # Get existing box
            response = box_table.get_item(
                Key={
                    'customer_id': customer_id,
                    'room_id#box_id': box_id
                }
            )
            
            if not response.get('Item'):
                return create_response(404, {'error': 'Box not found'})
            
            existing_item = response['Item']
            timestamp = datetime.utcnow().isoformat()
            
            # Add to history
            history_entry = {
                'action': body['action'],
                'timestamp': timestamp,
                'weight': body.get('weight'),
                'notes': body.get('notes')
            }
            
            existing_item['history'].append(history_entry)
            existing_item['updated_at'] = timestamp
            existing_item['action'] = body['action']
            if 'weight' in body:
                existing_item['weight'] = body['weight']
            
            # Update box
            box_table.put_item(Item=existing_item)
            return create_response(200, existing_item)
            
        # DELETE box
        elif http_method == 'DELETE':
            customer_id = event['pathParameters']['customer_id']
            box_id = event['pathParameters']['room_id#box_id']
            
            # Check if box exists
            response = box_table.get_item(
                Key={
                    'customer_id': customer_id,
                    'room_id#box_id': box_id
                }
            )
            
            if not response.get('Item'):
                return create_response(404, {'error': 'Box not found'})
            
            # Delete box
            box_table.delete_item(
                Key={
                    'customer_id': customer_id,
                    'room_id#box_id': box_id
                }
            )
            return create_response(200, {'message': 'Box deleted successfully'})
            
    except Exception as e:
        return create_response(500, {'error': str(e)})
