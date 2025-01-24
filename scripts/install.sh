#!/bin/bash

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print status messages
print_status() {
    echo -e "${YELLOW}[STATUS]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_progress() {
    echo -e "${BLUE}[PROGRESS]${NC} $1"
}

# Check if environment and region are provided
if [ "$#" -ne 2 ]; then
    print_error "Missing required parameters"
    echo "Usage: $0 <environment> <region>"
    echo "Example: $0 test ap-southeast-2"
    exit 1
fi

ENVIRONMENT=$1
REGION=$2

print_status "Starting installation for environment: $ENVIRONMENT, region: $REGION"

# Step 1: Deploy Infrastructure
print_status "Step 1/2: Deploying Infrastructure"
if ! ./scripts/deploy-auth.sh "$ENVIRONMENT" "$REGION"; then
    print_error "Infrastructure deployment failed"
    exit 1
fi
print_success "Infrastructure deployment completed"

# Step 2: Update Lambda Function
print_status "Step 2/2: Updating Lambda Function"
if ! ./scripts/update-lambda.sh "$ENVIRONMENT" "$REGION"; then
    print_error "Lambda function update failed"
    exit 1
fi
print_success "Lambda function update completed"

# Verify Installation
print_status "Verifying installation..."

# Check CloudFormation Stack
STACK_NAME="coolroom-api-auth-$ENVIRONMENT"
STACK_STATUS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" --query 'Stacks[0].StackStatus' --output text)
if [ "$STACK_STATUS" != "CREATE_COMPLETE" ] && [ "$STACK_STATUS" != "UPDATE_COMPLETE" ]; then
    print_error "Stack status is not healthy: $STACK_STATUS"
    exit 1
fi
print_progress "CloudFormation Stack Status: $STACK_STATUS"

# Check Lambda Function
FUNCTION_NAME="coolroom-auth-$ENVIRONMENT"
FUNCTION_STATE=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.State' --output text)
FUNCTION_LAST_UPDATE=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.LastModified' --output text)
CODE_SIZE=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.CodeSize' --output text)

if [ "$FUNCTION_STATE" != "Active" ]; then
    print_error "Lambda function is not active: $FUNCTION_STATE"
    exit 1
fi

print_progress "Lambda Function Status:"
print_progress "- State: $FUNCTION_STATE"
print_progress "- Last Updated: $FUNCTION_LAST_UPDATE"
print_progress "- Code Size: $CODE_SIZE bytes"

# Check API Gateway
API_ID=$(aws cloudformation describe-stacks --stack-name "coolroom-api-core-$ENVIRONMENT" --region "$REGION" --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayId`].OutputValue' --output text)
STAGE_NAME="$ENVIRONMENT"

if ! aws apigateway get-stage --rest-api-id "$API_ID" --stage-name "$STAGE_NAME" --region "$REGION" &>/dev/null; then
    print_error "API Gateway stage not found"
    exit 1
fi
print_progress "API Gateway stage verified"

print_success "Installation completed successfully!"
print_status "You can now test the API endpoint"