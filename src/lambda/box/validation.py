import re
from datetime import datetime

def validate_box_id(box_id):
    pattern = r'^ROOM[0-9]+#BOX[0-9A-Za-z]+$'
    return bool(re.match(pattern, box_id))

def validate_weight(weight):
    return isinstance(weight, (int, float)) and 0 <= weight <= 1000  # Max 1000kg

def validate_action(action):
    valid_actions = ['IN', 'OUT', 'UPDATE', 'MOVE', 'INSPECT']  # Added more actions
    return action in valid_actions

def validate_variety(variety):
    valid_varieties = ['Potato', 'Onion', 'Carrot', 'Other']
    return variety in valid_varieties

def validate_temperature(temp):
    return isinstance(temp, (int, float)) and -5 <= temp <= 15  # Valid cold storage range

def validate_box_input(data, is_batch=False):
    errors = []
    
    # Required fields
    required_fields = ['customer_id', 'room_id#box_id', 'action']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Validate box_id format
    if not validate_box_id(data['room_id#box_id']):
        errors.append("Invalid box_id format. Should be ROOMX#BOXYYY")
    
    # Validate action
    if not validate_action(data['action']):
        errors.append("Invalid action. Must be IN, OUT, UPDATE, MOVE, or INSPECT")
    
    # Validate weight if present
    if 'weight' in data and not validate_weight(data['weight']):
        errors.append("Invalid weight. Must be between 0 and 1000 kg")
    
    # Validate variety if present
    if 'variety' in data and not validate_variety(data['variety']):
        errors.append("Invalid variety. Must be Potato, Onion, Carrot, or Other")
    
    # Validate temperature if present
    if 'temperature' in data and not validate_temperature(data['temperature']):
        errors.append("Invalid temperature. Must be between -5°C and 15°C")
    
    # Additional batch validation
    if is_batch and 'batch
cat > src/lambda/box/handler.py << EOF
import json
import os
import boto3
from datetime import datetime, timedelta
from decimal import Decimal
from validation import validate_box_input, validate_batch_input
from boto3.dynamodb.conditions import Key, Attr

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
        'body': json.dumps(body, default=str)
    }

def check_user_exists(customer_id):
    response = user_table.get_item(Key={'customer_id': customer_id})
    return bool(response.get('Item'))

def get_room_statistics(customer_id, room_id):
    response = box_table.query(
        KeyConditionExpression=Key('customer_id').eq(customer_id) & 
                             Key('room_id#box_id').begins_with(f"{room_id}#"),
        FilterExpression=Attr('action').eq('IN')
    )
    
    total_weight = sum(item.get('weight', 0) for item in response['Items'])
    box_count = len(response['Items'])
    
    return {
        'room_id': room_id,
        'total_weight': total_weight,
        'box_count': box_count,
        'average_weight': total_weight / box_count if box_count > 0 else 0
    }

def handler(event, context):
    try:
        http_method = event['httpMethod']
        
        # New endpoint for room statistics
        if event.get('resource') == '/box/stats/{customer_id}/{room_id}':
            customer_id = event['pathParameters']['customer_id']
            room_id = event['pathParameters']['room_id']
            stats = get_room_statistics(customer_id, room_id)
            return create_response(200, stats)
            
        # Batch operations endpoint
        elif event.get('resource') == '/box/batch':
            if http_method == 'POST':
                body = json.loads(event['body'])
                
                # Validate batch input
                is_valid, errors = validate_batch_input(body)
                if not is_valid:
                    return create_response(400, {'errors': errors})
                
                # Process batch
                timestamp = datetime.utcnow().isoformat()
                batch_id = f"BATCH_{timestamp}"
                
                with box_table.batch_writer() as batch:
                    for item in body:
                        item['created_at'] = timestamp
                        item['updated_at'] = timestamp
                        item['batch_id'] = batch_id
                        item['history'] = [{
                            'action': item['action'],
                            'timestamp': timestamp,
                            'weight': item.get('weight'),
                            'temperature': item.get('temperature'),
                            'notes': item.get('notes')
                        }]
                        batch.put_item(Item=item)
                
                return create_response(201, {
                    'message': f'Successfully processed {len(body)} items',
                    'batch_id': batch_id
                })
        
        # Search endpoint
        elif event.get('resource') == '/box/search':
            params = event.get('queryStringParameters', {}) or {}
            
            # Build filter expression
            filter_expressions = []
            expression_values = {}
            
            if 'variety' in params:
                filter_expressions.append('variety = :variety')
                expression_values[':variety'] = params['variety']
                
            if 'min_weight' in params:
                filter_expressions.append('weight >= :min_weight')
                expression_values[':min_weight'] = Decimal(params['min_weight'])
                
            if 'max_weight' in params:
                filter_expressions.append('weight <= :max_weight')
                expression_values[':max_weight'] = Decimal(params['max_weight'])
                
            if 'action' in params:
                filter_expressions.append('action = :action')
                expression_values[':action'] = params['action']
            
            # Execute search
            if filter_expressions:
                filter_expression = ' AND '.join(filter_expressions)
                response = box_table.scan(
                    FilterExpression=filter_expression,
                    ExpressionAttributeValues=expression_values
                )
            else:
                response = box_table.scan()
mkdir -p tests/{unit,integration,load}
cat > tests/unit/test_validation.py << EOF
import unittest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src/lambda'))
from box.validation import validate_box_input, validate_batch_input
from user.validation import validate_user_input

class TestValidation(unittest.TestCase):
    def test_box_validation(self):
        # Valid box data
        valid_box = {
            'customer_id': 'CUST001',
            'room_id#box_id': 'ROOM1#BOX001',
            'action': 'IN',
            'weight': 50,
            'variety': 'Potato',
            'temperature': 5
        }
        is_valid, errors = validate_box_input(valid_box)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Invalid box data
        invalid_box = {
            'customer_id': 'CUST001',
            'room_id#box_id': 'INVALID',  # Invalid format
            'action': 'INVALID',  # Invalid action
            'weight': -1,  # Invalid weight
            'temperature': 20  # Invalid temperature
        }
        is_valid, errors = validate_box_input(invalid_box)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)

    def test_batch_validation(self):
        # Test batch size limit
        large_batch = [{'customer_id': f'CUST{i}', 
                       'room_id#box_id': f'ROOM1#BOX{i:03d}',
                       'action': 'IN'} for i in range(30)]
        is_valid, errors = validate_batch_input(large_batch)
        self.assertFalse(is_valid)
        self.assertTrue(any('batch size' in str(e).lower() for e in errors))

    def test_user_validation(self):
        # Valid user data
        valid_user = {
            'customer_id': 'CUST001',
            'company_name': 'Test Company',
            'email': 'test@example.com'
        }
        is_valid, errors = validate_user_input(valid_user)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        # Invalid user data
        invalid_user = {
            'customer_id': 'C',  # Too short
            'company_name': 'T',  # Too short
            'email': 'invalid-email'  # Invalid format
        }
        is_valid, errors = validate_user_input(invalid_user)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)

if __name__ == '__main__':
    unittest.main()
