#!/bin/bash

# Exit on error
set -e

# Configuration
ENVIRONMENT=${1:-dev}
REGION=${2:-ap-southeast-2}
STACK_NAME="coolroom-auth-${ENVIRONMENT}"
TEMPLATE_FILE="infrastructure/cloudformation/components/auth-resources.yaml"
S3_BUCKET="coolroom-lambda-${REGION}"
LAMBDA_CODE_PATH="src/lambda"
JWT_SECRET=$(openssl rand -base64 32)

echo "Deploying authentication resources to ${ENVIRONMENT} environment..."

# Create virtual environment and install dependencies
echo "Installing dependencies..."
python3 -m venv venv
source venv/bin/activate
pip install -r ${LAMBDA_CODE_PATH}/requirements.txt

# Package Lambda function
echo "Packaging Lambda function..."
cd ${LAMBDA_CODE_PATH}
zip -r ../../auth_handler.zip auth_handler.py
cd ../..

# Upload Lambda package to S3
echo "Uploading Lambda package to S3..."
aws s3 cp auth_handler.zip s3://${S3_BUCKET}/auth_handler.zip

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file ${TEMPLATE_FILE} \
  --stack-name ${STACK_NAME} \
  --parameter-overrides \
    Environment=${ENVIRONMENT} \
    JwtSecret=${JWT_SECRET} \
  --capabilities CAPABILITY_NAMED_IAM

# Clean up
rm auth_handler.zip
deactivate
rm -rf venv

echo "Deployment complete!"
echo "JWT Secret (save this securely): ${JWT_SECRET}"