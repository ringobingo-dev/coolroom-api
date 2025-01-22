import re

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_customer_id(customer_id):
    pattern = r'^[A-Za-z0-9][-A-Za-z0-9_]{2,20}$'
    return bool(re.match(pattern, customer_id))

def validate_user_input(data):
    errors = []
    
    # Required fields
    required_fields = ['customer_id', 'company_name', 'email']
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
        
    # Validate customer_id format
    if not validate_customer_id(data['customer_id']):
        errors.append("Invalid customer_id format")
    
    # Validate email format
    if not validate_email(data['email']):
        errors.append("Invalid email format")
    
    # Validate company_name length
    if len(data['company_name']) < 2 or len(data['company_name']) > 100:
        errors.append("Company name must be between 2 and 100 characters")
    
    return len(errors) == 0, errors
