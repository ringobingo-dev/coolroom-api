# CoolRoom API Project Structure

## Directory Structure
```
coolroom-api/
├── infrastructure/           # Infrastructure as Code (CloudFormation)
│   └── cloudformation/
│       └── components/      # CloudFormation templates
├── scripts/                 # Deployment and utility scripts
├── src/                     # Source code
│   ├── lambda/             # Lambda functions
│   └── lib/                # Shared libraries
├── tests/                   # Test files
├── config/                  # Configuration files
├── api-docs/               # API documentation
└── .github/                # GitHub Actions workflows
```

## Key Files
- `infrastructure/cloudformation/components/core-infrastructure.yaml`: Core API Gateway setup
- `infrastructure/cloudformation/components/auth-resources.yaml`: Authentication resources
- `scripts/deploy-core.sh`: Core infrastructure deployment script
- `scripts/deploy-auth.sh`: Authentication deployment script
- `src/lambda/auth_handler.py`: Authentication Lambda function
- `src/lambda/requirements.txt`: Python dependencies

## Environment Setup
- Python virtual environment (venv)
- AWS CLI configuration
- Environment variables (.env files)

## Deployment Process
1. Deploy core infrastructure
2. Deploy authentication resources
3. Configure API Gateway
4. Deploy Lambda functions

## Clean-up Tasks
- [x] Remove duplicate files
- [x] Consolidate deployment scripts
- [x] Organize CloudFormation templates
- [x] Set up proper environment configuration
- [x] Clean up temporary files 