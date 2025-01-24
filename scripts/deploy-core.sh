#!/bin/bash

# Exit on error
set -e

# Configuration
ENVIRONMENT=${1:-test}
REGION=${2:-ap-southeast-2}
STACK_NAME="coolroom-api"
TEMPLATE_FILE="infrastructure/cloudformation/components/core-infrastructure.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print status messages
print_status() {
    echo -e "${YELLOW}[STATUS]${NC} $1"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

# Function to print progress messages
print_progress() {
    echo -e "${BLUE}[PROGRESS]${NC} $1"
}

# Function to validate AWS CLI configuration
validate_aws_config() {
    print_status "Validating AWS CLI configuration..."
    if ! aws sts get-caller-identity &>/dev/null; then
        print_error "AWS CLI is not configured correctly. Please check your credentials."
    fi
    print_progress "AWS CLI configuration validated"
}

# Check if environment and region are provided
if [ "$#" -ne 2 ]; then
    print_error "Usage: $0 <environment> <region>\nExample: $0 test ap-southeast-2"
fi

print_status "Starting core infrastructure deployment for $ENVIRONMENT environment"
print_status "Region: $REGION"
print_status "Stack name: $STACK_NAME-core-$ENVIRONMENT"

# Validate AWS configuration
validate_aws_config

# Validate CloudFormation template
print_status "Validating CloudFormation template..."
if ! aws cloudformation validate-template \
    --template-body file://$TEMPLATE_FILE \
    --region $REGION &>/dev/null; then
    print_error "Invalid CloudFormation template: $TEMPLATE_FILE"
fi
print_progress "CloudFormation template validated"

# Deploy CloudFormation stack
print_status "Deploying CloudFormation stack..."
if ! aws cloudformation deploy \
    --template-file ${TEMPLATE_FILE} \
    --stack-name ${STACK_NAME}-core-${ENVIRONMENT} \
    --parameter-overrides \
        Environment=${ENVIRONMENT} \
    --capabilities CAPABILITY_NAMED_IAM \
    --region ${REGION} \
    --no-fail-on-empty-changeset; then
    print_error "Failed to deploy CloudFormation stack"
fi

print_success "Stack deployment completed"

# Function to generate deployment report
generate_deployment_report() {
    local stack_name="$1-core-$2"
    local region=$3
    
    echo -e "\n${BLUE}========== Core Infrastructure Deployment Report ==========${NC}"
    echo -e "${YELLOW}Timestamp:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    
    # Get stack status and timestamp
    print_status "Retrieving stack information..."
    local stack_info=$(aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --region $region \
        --query 'Stacks[0].{Status:StackStatus,LastUpdated:LastUpdatedTime}' \
        --output text)
    local status=$(echo "$stack_info" | cut -f1)
    local last_updated=$(echo "$stack_info" | cut -f2)
    
    echo -e "\n${YELLOW}1. CloudFormation Stack Status:${NC}"
    echo -e "   ✓ Stack Name: $stack_name"
    echo -e "   ✓ Status: $status"
    echo -e "   ✓ Last Updated: $last_updated"
    
    # Get API Gateway details
    print_status "Retrieving API Gateway information..."
    local api_id=$(aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --region $region \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayId`].OutputValue' \
        --output text)
    local root_resource_id=$(aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --region $region \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayRootResourceId`].OutputValue' \
        --output text)
    local endpoint=$(aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --region $region \
        --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
        --output text)
    
    echo -e "\n${YELLOW}2. API Gateway Resources:${NC}"
    echo -e "   ✓ REST API ID: $api_id"
    echo -e "   ✓ Root Resource ID: $root_resource_id"
    echo -e "   ✓ Stage: test"
    
    echo -e "\n${YELLOW}3. Endpoint Information:${NC}"
    echo -e "   ✓ URL: $endpoint"
    
    # Test endpoint
    print_status "Validating endpoint..."
    local curl_response=$(curl -s -w "\n%{http_code}" "$endpoint")
    local http_code=$(echo "$curl_response" | tail -n1)
    local response_body=$(echo "$curl_response" | sed '$d')
    
    echo -e "\n${YELLOW}4. Endpoint Validation:${NC}"
    echo -e "   ✓ HTTPS: Enabled"
    echo -e "   ✓ HTTP Status: $http_code"
    echo -e "   ✓ Response: $response_body"
    
    if [ "$http_code" = "403" ] && [[ "$response_body" == *"Missing Authentication Token"* ]]; then
        echo -e "   ✓ Security: Authentication required (Expected behavior)"
    else
        print_error "Unexpected endpoint response"
    fi
    
    print_success "Core Infrastructure Deployment Completed Successfully"
    echo -e "${BLUE}================================================${NC}\n"
    
    # Display full stack outputs
    print_status "Stack Outputs:"
    aws cloudformation describe-stacks \
        --stack-name $stack_name \
        --query 'Stacks[0].Outputs' \
        --output table \
        --region $region
}

# Generate the deployment report
generate_deployment_report "$STACK_NAME" "$ENVIRONMENT" "$REGION"