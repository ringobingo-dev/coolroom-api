#!/bin/bash
set -e

echo "🚀 Starting Dev Environment Deployment"

# Load dev configuration
CONFIG_FILE="../config/dev.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: dev.json configuration file not found!"
    exit 1
fi

# Set variables from config
ENVIRONMENT="dev"
REGION="ap-southeast-2"
STACK_NAME="coolroom-dev"
DEPLOYMENT_BUCKET="coolroom-dev-deployment-$(date +%s)"

echo "📋 Deployment Configuration:"
echo "Environment: $ENVIRONMENT"
echo "Region: $REGION"
echo "Stack Name: $STACK_NAME"
