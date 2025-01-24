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
FUNCTION_NAME="coolroom-auth-$ENVIRONMENT"

print_status "Starting Lambda function update for $FUNCTION_NAME"

# Validate Lambda function exists
print_status "Validating Lambda function..."
if ! aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" &> lambda_function_check.log; then
    print_error "Lambda function $FUNCTION_NAME not found"
    cat lambda_function_check.log
    exit 1
fi

# Check current function state
CURRENT_STATE=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.State' --output text)
if [ "$CURRENT_STATE" != "Active" ]; then
    print_error "Function is not in Active state (current state: $CURRENT_STATE)"
    exit 1
fi
print_progress "Lambda function exists and is Active"

# Create deployment package
print_status "Creating deployment package..."
if ! mkdir -p .build; then
    print_error "Failed to create build directory"
    exit 1
fi

# Copy handler
if ! cp src/handlers/auth_handler.py .build/; then
    print_error "Failed to copy auth handler"
    rm -rf .build
    exit 1
fi
print_progress "Auth handler copied"

# Install dependencies
print_status "Installing dependencies..."
if ! python3 -m pip install --platform manylinux2014_x86_64 \
    --target=.build \
    --implementation cp \
    --python-version 3.9 \
    --only-binary=:all: \
    --upgrade \
    -r requirements.txt 2>&1 | tee pip_install.log; then
    print_error "Failed to install dependencies. Check pip_install.log for details"
    cat pip_install.log
    rm -rf .build
    exit 1
fi

# Verify dependencies
print_status "Verifying dependencies..."
for pkg in "PyJWT" "aws_lambda_powertools"; do
    if ! ls .build/${pkg}* >/dev/null 2>&1; then
        print_error "Required package ${pkg} not found in build directory"
        rm -rf .build
        exit 1
    fi
    print_progress "Found package: ${pkg}"
done

# Create zip package
print_status "Creating zip package..."
cd .build || exit 1
if ! zip -r ../auth-function.zip . > ../zip_creation.log 2>&1; then
    print_error "Failed to create zip package"
    cat ../zip_creation.log
    cd ..
    rm -rf .build auth-function.zip
    exit 1
fi
cd ..

# Verify zip contents
print_status "Verifying zip package..."
ZIP_SIZE=$(stat -f%z "auth-function.zip" 2>/dev/null)
if [ ! -f "auth-function.zip" ] || [ ! -s "auth-function.zip" ] || [ "$ZIP_SIZE" -lt 1000000 ]; then
    print_error "Zip package seems too small (${ZIP_SIZE} bytes). Expected size > 1MB"
    rm -rf .build auth-function.zip
    exit 1
fi
print_progress "Created deployment package (size: $ZIP_SIZE bytes)"

# Update function code
print_status "Updating Lambda function code..."
if ! aws lambda update-function-code \
    --function-name "$FUNCTION_NAME" \
    --zip-file fileb://auth-function.zip \
    --region "$REGION" 2>&1 | tee lambda_update.log; then
    print_error "Failed to update Lambda function code. Details below:"
    cat lambda_update.log
    rm -rf .build auth-function.zip
    exit 1
fi

# Wait for update to complete
print_status "Waiting for function update to complete..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    FUNCTION_STATE=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.State' --output text)
    LAST_UPDATE_STATUS=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.LastUpdateStatus' --output text)
    
    print_progress "Current state: $FUNCTION_STATE, Update status: $LAST_UPDATE_STATUS"
    
    if [ "$FUNCTION_STATE" = "Active" ] && [ "$LAST_UPDATE_STATUS" = "Successful" ]; then
        break
    elif [ "$LAST_UPDATE_STATUS" = "Failed" ]; then
        print_error "Function update failed"
        exit 1
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    print_error "Timeout waiting for function update"
    exit 1
fi

# Final verification
FINAL_STATE=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.State' --output text)
FINAL_CODE_SIZE=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.CodeSize' --output text)
FINAL_LAST_MODIFIED=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region "$REGION" --query 'Configuration.LastModified' --output text)

print_progress "Final function state: $FINAL_STATE"
print_progress "Code size: $FINAL_CODE_SIZE bytes"
print_progress "Last modified: $FINAL_LAST_MODIFIED"

if [ "$FINAL_STATE" != "Active" ]; then
    print_error "Function is not in Active state after update"
    exit 1
fi

print_success "Lambda function code updated successfully"

# Cleanup
rm -rf .build auth-function.zip pip_install.log zip_creation.log lambda_update.log lambda_function_check.log