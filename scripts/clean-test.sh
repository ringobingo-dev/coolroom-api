#!/bin/bash

# Exit on error
set -e

# Configuration
ENVIRONMENT=${1:-test}
REGION=${2:-ap-southeast-2}
STACK_NAME="coolroom-api"
CORE_STACK="${STACK_NAME}-core-${ENVIRONMENT}"
AUTH_STACK="${STACK_NAME}-auth-${ENVIRONMENT}"
S3_BUCKET="coolroom-lambda-${REGION}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    local level=$1
    shift
    local message=$@
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    case $level in
        "INFO")
            echo -e "${BLUE}[INFO]${NC} ${timestamp} - $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} ${timestamp} - $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} ${timestamp} - $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} ${timestamp} - $message"
            ;;
    esac
}

# Validation function
validate() {
    log "INFO" "Starting validation checks..."
    
    # Check AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        log "ERROR" "AWS CLI is not installed"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        log "ERROR" "AWS credentials are not configured"
        exit 1
    fi
    
    # Check required files exist
    local required_files=(
        "infrastructure/cloudformation/components/core-infrastructure.yaml"
        "infrastructure/cloudformation/components/auth-resources.yaml"
        "scripts/deploy-core.sh"
        "scripts/deploy-auth.sh"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            log "ERROR" "Required file not found: $file"
            exit 1
        fi
    done
    
    log "SUCCESS" "Validation checks passed"
}

# Clean up function
cleanup() {
    local stack_name=$1
    log "INFO" "Checking stack: $stack_name"
    
    if aws cloudformation describe-stacks --stack-name $stack_name --region $REGION &> /dev/null; then
        log "INFO" "Deleting stack: $stack_name"
        aws cloudformation delete-stack --stack-name $stack_name --region $REGION
        aws cloudformation wait stack-delete-complete --stack-name $stack_name --region $REGION
        log "SUCCESS" "Stack deleted: $stack_name"
    else
        log "INFO" "Stack does not exist: $stack_name"
    fi
}

# S3 cleanup function
cleanup_s3() {
    log "INFO" "Checking S3 bucket: $S3_BUCKET"
    
    if aws s3api head-bucket --bucket $S3_BUCKET 2>/dev/null; then
        log "INFO" "Emptying S3 bucket: $S3_BUCKET"
        aws s3 rm s3://${S3_BUCKET} --recursive
        log "INFO" "Deleting S3 bucket: $S3_BUCKET"
        aws s3api delete-bucket --bucket $S3_BUCKET --region $REGION
        log "SUCCESS" "S3 bucket deleted: $S3_BUCKET"
    else
        log "INFO" "S3 bucket does not exist: $S3_BUCKET"
    fi
}

main() {
    log "INFO" "Starting cleanup procedure for environment: $ENVIRONMENT"
    
    # Run validations
    validate
    
    # Clean up stacks in reverse order
    cleanup $AUTH_STACK
    cleanup $CORE_STACK
    
    # Clean up S3 bucket
    cleanup_s3
    
    log "SUCCESS" "Cleanup completed successfully"
    log "INFO" "Environment is ready for testing"
    
    # Print summary
    echo -e "\n${BLUE}Cleanup Summary:${NC}"
    echo -e "Environment: $ENVIRONMENT"
    echo -e "Region: $REGION"
    echo -e "Core Stack: $CORE_STACK"
    echo -e "Auth Stack: $AUTH_STACK"
    echo -e "S3 Bucket: $S3_BUCKET"
}

# Run main function
main