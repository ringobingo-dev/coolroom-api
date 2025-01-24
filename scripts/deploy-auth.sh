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

# Function to print success messages
print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Function to print error messages
print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo -e "${RED}[ERROR]${NC} Deployment failed. Check the logs above for details."
}

# Function to print detailed progress
print_progress() {
    echo -e "${BLUE}[PROGRESS]${NC} $1"
}

# Function to check command status
check_command() {
    if [ $? -ne 0 ]; then
        print_error "$1"
        return 1
    fi
    return 0
}

# Function to validate AWS CLI configuration
validate_aws_config() {
    print_status "Validating AWS CLI configuration..."
    if ! aws sts get-caller-identity &>/dev/null; then
        print_error "AWS CLI is not configured correctly. Please check your credentials."
        exit 1
    fi
    print_progress "AWS CLI configuration validated"
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
STACK_NAME="coolroom-api-auth-$ENVIRONMENT"
CORE_STACK_NAME="coolroom-api-core-$ENVIRONMENT"
TEMPLATE_FILE="infrastructure/cloudformation/components/auth-infrastructure.yaml"

print_status "Starting auth infrastructure deployment for $ENVIRONMENT environment"
print_status "Region: $REGION"
print_status "Stack name: $STACK_NAME"

# Validate AWS configuration
validate_aws_config

# Validate requirements
print_status "Validating requirements..."

# Check if python3 is available and get version
PYTHON_VERSION=$(python3 --version 2>&1)
if ! command -v python3 &> /dev/null; then
    print_error "python3 is required but not found"
    exit 1
fi
print_progress "Using $PYTHON_VERSION"

# Check if pip is available and get version
PIP_VERSION=$(python3 -m pip --version 2>&1)
print_progress "Using $PIP_VERSION"

# Check if requirements.txt exists and is not empty
if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt not found"
    exit 1
fi
if [ ! -s "requirements.txt" ]; then
    print_error "requirements.txt is empty"
    exit 1
fi
print_progress "requirements.txt validated"

# Check if auth handler exists and is not empty
if [ ! -f "src/handlers/auth_handler.py" ]; then
    print_error "auth_handler.py not found in src/handlers/"
    exit 1
fi
if [ ! -s "src/handlers/auth_handler.py" ]; then
    print_error "auth_handler.py is empty"
    exit 1
fi
print_progress "auth_handler.py validated"

# Check if CloudFormation template exists and is valid
if [ ! -f "$TEMPLATE_FILE" ]; then
    print_error "CloudFormation template not found: $TEMPLATE_FILE"
    exit 1
fi

# Validate CloudFormation template
print_status "Validating CloudFormation template..."
if ! aws cloudformation validate-template \
    --template-body file://$TEMPLATE_FILE \
    --region $REGION &>/dev/null; then
    print_error "Invalid CloudFormation template"
    exit 1
fi
print_progress "CloudFormation template validated"

# Create deployment package
print_status "Creating deployment package..."
if ! mkdir -p .build; then
    print_error "Failed to create build directory"
    exit 1
fi
print_progress "Build directory created"

if ! cp src/handlers/auth_handler.py .build/; then
    print_error "Failed to copy auth handler"
    rm -rf .build
    exit 1
fi
print_progress "Auth handler copied"

print_status "Installing dependencies..."
# Capture pip output and display it
if ! /usr/bin/python3 -m pip install -r requirements.txt -t .build/ 2>&1 | tee pip_install.log; then
    print_error "Failed to install dependencies. Check pip_install.log for details"
    rm -rf .build
    exit 1
fi

# Verify key dependencies are installed
print_status "Verifying dependencies..."
for pkg in "PyJWT" "aws_lambda_powertools"; do
    if ! ls .build/${pkg}* >/dev/null 2>&1; then
        print_error "Required package ${pkg} not found in build directory"
        rm -rf .build
        exit 1
    fi
    print_progress "Found package: ${pkg}"
done

print_status "Creating zip package..."
cd .build || exit 1
if ! zip -r ../auth-function.zip . 2>&1 | tee ../zip_creation.log; then
    print_error "Failed to create zip package. Check zip_creation.log for details"
    cd ..
    rm -rf .build
    exit 1
fi
cd ..

# Verify zip file contents
print_status "Verifying zip package..."
ZIP_CONTENTS=$(unzip -l auth-function.zip)
for pkg in "PyJWT" "aws_lambda_powertools" "auth_handler.py"; do
    if ! echo "$ZIP_CONTENTS" | grep -q "$pkg"; then
        print_error "Required file/package ${pkg} not found in zip"
        rm -rf .build auth-function.zip
        exit 1
    fi
    print_progress "Verified package: ${pkg}"
done

# Get and display zip size
ZIP_SIZE=$(stat -f%z "auth-function.zip" 2>/dev/null)
if [ ! -f "auth-function.zip" ] || [ ! -s "auth-function.zip" ] || [ "$ZIP_SIZE" -lt 1000000 ]; then
    print_error "Zip package seems too small (${ZIP_SIZE} bytes). Expected size > 1MB"
    rm -rf .build auth-function.zip
    exit 1
fi
print_progress "Created deployment package (size: $ZIP_SIZE bytes)"

print_success "Deployment package created successfully"
rm -rf .build

# Check if core stack exists
print_status "Checking core stack dependency..."
if ! aws cloudformation describe-stacks --stack-name $CORE_STACK_NAME --region $REGION &>/dev/null; then
    print_error "Core stack $CORE_STACK_NAME not found"
    exit 1
fi
print_progress "Core stack validated"

# Deploy CloudFormation stack
print_status "Deploying CloudFormation stack..."
if ! aws cloudformation deploy \
    --template-file $TEMPLATE_FILE \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        Environment=$ENVIRONMENT \
        CoreStackName=$CORE_STACK_NAME \
    --capabilities CAPABILITY_IAM \
    --region $REGION 2>&1 | tee cloudformation_deploy.log; then
    print_error "Failed to deploy CloudFormation stack. Check cloudformation_deploy.log for details"
    exit 1
fi

print_success "Stack deployment completed"

# Update Lambda function code
print_status "Updating Lambda function code..."
FUNCTION_NAME="coolroom-auth-$ENVIRONMENT"

# Check if Lambda function exists and is in correct state
aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > lambda_function_check.log 2>&1

# Update function code
echo "Updating Lambda function code..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://auth-function.zip \
    --region $REGION > lambda_update.log 2>&1

if [ $? -ne 0 ]; then
    echo "Failed to update Lambda function code. Check lambda_update.log for details."
    exit 1
fi

# Get function state and last update
aws lambda get-function --function-name $FUNCTION_NAME --region $REGION > lambda_state_check.log 2>&1

# Final verification
FINAL_STATE=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.State' --output text)
FINAL_CODE_SIZE=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.CodeSize' --output text)
FINAL_LAST_MODIFIED=$(aws lambda get-function --function-name $FUNCTION_NAME --region $REGION --query 'Configuration.LastModified' --output text)

print_progress "Final function state: $FINAL_STATE"
print_progress "Code size: $FINAL_CODE_SIZE bytes"
print_progress "Last modified: $FINAL_LAST_MODIFIED"

if [ "$FINAL_STATE" != "Active" ]; then
    print_error "Function is not in Active state after update"
    exit 1
fi

if [ "$FINAL_CODE_SIZE" -lt 1000000 ]; then
    print_error "Deployed code size seems too small ($FINAL_CODE_SIZE bytes). Expected > 1MB"
    exit 1
fi

print_success "Lambda function code updated successfully"

# Only remove logs if deployment was successful
if [ $? -eq 0 ]; then
    rm -f lambda_*.log
fi

# Display stack outputs
print_status "Deployment complete. Stack outputs:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query 'Stacks[0].Outputs' \
    --output table \
    --region $REGION 