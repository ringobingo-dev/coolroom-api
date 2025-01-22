#!/bin/bash
set -e

ENVIRONMENT="dev"
REGION="ap-southeast-2"
PROFILE="coolroom-dev"
STACK_NAME="coolroom-${ENVIRONMENT}"

# Get API URL
echo "Getting API URL..."
API_URL=$(aws cloudformation describe-stacks \
    --stack-name ${STACK_NAME} \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text \
    --region ${REGION} \
    --profile ${PROFILE})

echo "API URL: ${API_URL}"

# Test 1: Create user with all fields
echo -e "\nTest 1: Creating user with all fields..."
CREATE_RESPONSE=$(curl -s -X POST \
    "${API_URL}/users" \
    -H 'Content-Type: application/json' \
    -d '{
        "email": "test@example.com",
        "name": "Test User",
        "phone": "+61412345678",
        "address": "123 Test St, Sydney NSW 2000",
        "preferences": {"notifications": "email"}
    }')
echo "Create Response: ${CREATE_RESPONSE}"

# Extract customer_id from response
CUSTOMER_ID=$(echo ${CREATE_RESPONSE} | jq -r '.user.customer_id')

# Test 2: Get user by customer_id
echo -e "\nTest 2: Getting user by customer_id..."
GET_RESPONSE=$(curl -s -X GET "${API_URL}/users/${CUSTOMER_ID}")
echo "Get Response: ${GET_RESPONSE}"

# Test 3: Verify in DynamoDB
echo -e "\nTest 3: Verifying DynamoDB record..."
DYNAMO_RESPONSE=$(aws dynamodb get-item \
    --table-name ${ENVIRONMENT}-User \
    --key "{\"customer_id\": {\"S\": \"${CUSTOMER_ID}\"}}" \
    --region ${REGION} \
    --profile ${PROFILE})
echo "DynamoDB Response: ${DYNAMO_RESPONSE}"

# Test 4: Try to create user with same email (should fail)
echo -e "\nTest 4: Testing duplicate email validation..."
DUPLICATE_RESPONSE=$(curl -s -X POST \
    "${API_URL}/users" \
    -H 'Content-Type: application/json' \
    -d '{
        "email": "test@example.com",
        "name": "Duplicate User",
        "phone": "+61412345679"
    }')
echo "Duplicate Email Response: ${DUPLICATE_RESPONSE}"

# Test 5: Try to create user with invalid email
echo -e "\nTest 5: Testing invalid email validation..."
INVALID_EMAIL_RESPONSE=$(curl -s -X POST \
    "${API_URL}/users" \
    -H 'Content-Type: application/json' \
    -d '{
        "email": "invalid-email",
        "name": "Invalid Email User",
        "phone": "+61412345670"
    }')
echo "Invalid Email Response: ${INVALID_EMAIL_RESPONSE}"

# Test 6: Try to create user with missing required field
echo -e "\nTest 6: Testing missing required field validation..."
MISSING_FIELD_RESPONSE=$(curl -s -X POST \
    "${API_URL}/users" \
    -H 'Content-Type: application/json' \
    -d '{
        "email": "test2@example.com",
        "phone": "+61412345671"
    }')
echo "Missing Field Response: ${MISSING_FIELD_RESPONSE}"

# Test 7: Try to get non-existent user
echo -e "\nTest 7: Testing non-existent user..."
NOT_FOUND_RESPONSE=$(curl -s -X GET "${API_URL}/users/non-existent-id")
echo "Not Found Response: ${NOT_FOUND_RESPONSE}"

echo -e "\nAll tests completed!"
