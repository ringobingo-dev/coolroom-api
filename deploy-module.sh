#!/bin/bash

# Configuration
ENV="dev"
REGION="ap-southeast-2"
STACK_NAME="next-customer-${ENV}"
DEPLOYMENT_BUCKET="coolroom-api-deployment-as"

echo "Starting deployment process..."

# Create build directory
mkdir -p .build

# Package Lambda function
echo "Packaging Lambda function..."
cd infrastructure/lambda && zip ../../.build/next_customer.zip next_customer.py && cd ../..

# Upload to S3
echo "Uploading to S3..."
aws s3 cp .build/next_customer.zip s3://${DEPLOYMENT_BUCKET}/${ENV}/lambda/

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
    --template-file infrastructure/cloudformation/next-customer-template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides Environment=$ENV DeploymentBucket=${DEPLOYMENT_BUCKET} \
    --capabilities CAPABILITY_IAM \
    --region $REGION

echo "Deployment complete!"
