#!/bin/bash

# Set environment
ENV="dev"
REGION="ap-southeast-2"
STACK_NAME="next-customer-${ENV}"
TEMPLATE_FILE="infrastructure/cloudformation/next-customer-template.yaml"
DEPLOYMENT_BUCKET="coolroom-api-deployment-as"

# Package Lambda code
echo "Packaging Lambda function..."
mkdir -p .build
zip -r .build/next-customer.zip infrastructure/lambda/next-customer.py

# Upload to S3
echo "Uploading to S3..."
aws s3 cp .build/next-customer.zip s3://${DEPLOYMENT_BUCKET}/${ENV}/lambda/

# Deploy CloudFormation
echo "Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file $TEMPLATE_FILE \
  --stack-name $STACK_NAME \
  --parameter-overrides Environment=$ENV DeploymentBucket=${DEPLOYMENT_BUCKET} \
  --capabilities CAPABILITY_IAM \
  --region $REGION

# Get API URL
API_URL=$(aws cloudformation describe-stacks \
  --stack-name $STACK_NAME \
  --query 'Stacks[0].Outputs[?OutputKey==`CustomerApiUrl`].OutputValue' \
  --output text \
  --region $REGION)

echo "Deployment complete. API URL: $API_URL"
