#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
REGION="us-east-1"
ENVIRONMENT="test"
TIMESTAMP=$(date +%Y%m%d%H%M)
STACK_PREFIX="warehouse-ui"
BACKUP_DIR="infrastructure/cloudformation/backup_$TIMESTAMP"

# Logging and error handling
log() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Pre-flight validation
validate_environment() {
    log "Validating environment..."
    aws sts get-caller-identity > /dev/null 2>&1 || error "Invalid AWS credentials"
    log "Environment validation complete"
}

# Backup current state
backup_current_state() {
    log "Creating backup of current state..."
    mkdir -p "$BACKUP_DIR"
    aws cloudformation describe-stacks \
        --query "Stacks[?contains(StackName, '$STACK_PREFIX')]" \
        --output json > "$BACKUP_DIR/current_state.json" 2>/dev/null || true
    log "Backup complete: $BACKUP_DIR"
}

# Resource validation
validate_resources() {
    log "Validating resources..."
    
    # Check for existing buckets
    local content_bucket="test-warehouse-ui-content-test-$TIMESTAMP"
    local logs_bucket="test-warehouse-ui-logs-test-$TIMESTAMP"
    
    aws s3api head-bucket --bucket "$content_bucket" 2>/dev/null && \
        error "Content bucket already exists: $content_bucket"
    aws s3api head-bucket --bucket "$logs_bucket" 2>/dev/null && \
        error "Logs bucket already exists: $logs_bucket"
        
    log "Resource validation complete"
}

# Stack deployment
deploy_stack() {
    local stack_name=$1
    local template=$2
    local parameters=$3
    
    log "Deploying stack: $stack_name"
    
    # Create stack
    aws cloudformation create-stack \
        --stack-name "$stack_name" \
        --template-body "file://infrastructure/cloudformation/components/$template" \
        --parameters $parameters \
        --capabilities CAPABILITY_IAM \
        --region $REGION
    
    log "Waiting for stack completion: $stack_name"
    aws cloudformation wait stack-create-complete \
        --stack-name "$stack_name" \
        --region $REGION || error "Stack creation failed: $stack_name"
    
    log "Stack deployment complete: $stack_name"
}

# Generate deployment report
generate_deployment_report() {
    log "Generating deployment report..."
    
    echo "
DEPLOYMENT REPORT
================
Date: $(date)
Environment: $ENVIRONMENT
Region: $REGION

Stack Status:
------------
$(aws cloudformation list-stacks \
    --query "StackSummaries[?contains(StackName, '$STACK_PREFIX')].[StackName,StackStatus]" \
    --output table)

S3 Buckets:
-----------
$(aws s3api list-buckets \
    --query "Buckets[?contains(Name, 'test-warehouse-ui')].[Name,CreationDate]" \
    --output table)

CloudFront Distribution:
----------------------
$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?contains(Origins.Items[0].Id, '$STACK_PREFIX')].[Id,DomainName,Status,Enabled]" \
    --output table)

WAF Configuration:
----------------
Web ACL ARN: $WAF_ARN

Important URLs:
-------------
CloudFront URL: https://$(aws cloudfront list-distributions \
    --query "DistributionList.Items[?contains(Origins.Items[0].Id, '$STACK_PREFIX')].DomainName" \
    --output text)
S3 Content Bucket: $S3_DOMAIN

Deployment Duration: $(($SECONDS / 60)) minutes and $(($SECONDS % 60)) seconds
"
}

# Main deployment process
main() {
    log "Starting deployment process..."
    
    validate_environment
    backup_current_state
    validate_resources
    
    # Deploy WAF stack
    deploy_stack "warehouse-ui-waf" "waf.yaml" \
        "ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
         ParameterKey=RateLimit,ParameterValue=2000"
    
    # Get WAF ARN
    WAF_ARN=$(aws cloudformation describe-stacks \
        --stack-name warehouse-ui-waf \
        --query 'Stacks[0].Outputs[?OutputKey==`WebACLArn`].OutputValue' \
        --output text \
        --region $REGION)
    
    # Deploy S3 stack
    deploy_stack "warehouse-ui-s3" "s3.yaml" \
        "ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
         ParameterKey=Timestamp,ParameterValue=$TIMESTAMP"
    
    # Get S3 domain name
    S3_DOMAIN=$(aws cloudformation describe-stacks \
        --stack-name warehouse-ui-s3 \
        --query 'Stacks[0].Outputs[?OutputKey==`TestBucketDomainName`].OutputValue' \
        --output text \
        --region $REGION)
    
    # Deploy CloudFront stack
    deploy_stack "warehouse-ui-cloudfront" "cloudfront.yaml" \
        "ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
         ParameterKey=WebACLArn,ParameterValue=$WAF_ARN \
         ParameterKey=S3BucketDomainName,ParameterValue=$S3_DOMAIN"
    
    log "Deployment process complete"
    generate_deployment_report
}

# Run the deployment
main
