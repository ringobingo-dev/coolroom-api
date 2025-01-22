#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_log() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Clean CloudFront distributions
cleanup_cloudfront() {
    print_log "Cleaning up CloudFront distributions..."
    
    local dist_id=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?contains(Origins.Items[0].Id, 'warehouse-ui')].Id" \
        --output text)
    
    if [ ! -z "$dist_id" ]; then
        print_log "Found CloudFront distribution: $dist_id"
        local etag=$(aws cloudfront get-distribution-config --id $dist_id --query 'ETag' --output text)
        print_log "Disabling distribution..."
        aws cloudfront get-distribution-config --id $dist_id | \
            jq '.DistributionConfig.Enabled = false' > disable.json
        aws cloudfront update-distribution \
            --id $dist_id \
            --distribution-config file://disable.json \
            --if-match $etag
        print_log "Waiting for distribution to be disabled..."
        aws cloudfront wait distribution-deployed --id $dist_id
        print_log "Deleting distribution..."
        etag=$(aws cloudfront get-distribution --id $dist_id --query 'ETag' --output text)
        aws cloudfront delete-distribution --id $dist_id --if-match $etag
        rm -f disable.json
    else
        print_log "No CloudFront distributions found"
    fi
}

# Clean S3 buckets
cleanup_s3() {
    print_log "Cleaning up S3 buckets..."
    
    local buckets=$(aws s3api list-buckets \
        --query "Buckets[?starts_with(Name, 'test-warehouse-ui')].[Name]" \
        --output text)
    
    for bucket in $buckets; do
        print_log "Cleaning bucket: $bucket"
        aws s3api list-object-versions \
            --bucket $bucket \
            --query '{Objects: Versions[].{Key:Key,VersionId:VersionId}}' \
            --output json | \
            jq 'if .Objects then . else {"Objects":[]} end' | \
            aws s3api delete-objects --bucket $bucket --delete file:///dev/stdin || true
        aws s3api list-object-versions \
            --bucket $bucket \
            --query '{Objects: DeleteMarkers[].{Key:Key,VersionId:VersionId}}' \
            --output json | \
            jq 'if .Objects then . else {"Objects":[]} end' | \
            aws s3api delete-objects --bucket $bucket --delete file:///dev/stdin || true
        print_log "Deleting bucket: $bucket"
        aws s3api delete-bucket --bucket $bucket || true
    done
}

# Clean WAF
cleanup_waf() {
    print_log "Cleaning up WAF..."
    
    local webacls=$(aws wafv2 list-web-acls \
        --scope CLOUDFRONT \
        --region us-east-1 \
        --query "WebACLs[?contains(Name, 'warehouse-ui')].[Name,Id,LockToken]" \
        --output text)
    
    if [ ! -z "$webacls" ]; then
        while read -r name id token; do
            print_log "Deleting WebACL: $name"
            aws wafv2 delete-web-acl \
                --name $name \
                --scope CLOUDFRONT \
                --region us-east-1 \
                --id $id \
                --lock-token $token || true
        done <<< "$webacls"
    else
        print_log "No WAF WebACLs found"
    fi
}

# Clean CloudFormation stacks
cleanup_stacks() {
    print_log "Cleaning up CloudFormation stacks..."
    
    local stacks="warehouse-ui-cloudfront warehouse-ui-s3 warehouse-ui-waf warehouse-ui-policies"
    
    for stack in $stacks; do
        if aws cloudformation describe-stacks --stack-name $stack 2>/dev/null; then
            print_log "Deleting stack: $stack"
            aws cloudformation delete-stack --stack-name $stack
            print_log "Waiting for stack deletion: $stack"
            aws cloudformation wait stack-delete-complete --stack-name $stack
        else
            print_log "Stack not found: $stack"
        fi
    done
}

main() {
    print_log "Starting cleanup process..."
    
    cleanup_cloudfront
    cleanup_s3
    cleanup_waf
    cleanup_stacks
    
    print_log "Cleanup complete"
    
    print_log "Verifying cleanup..."
    aws cloudformation list-stacks \
        --query "StackSummaries[?contains(StackName, 'warehouse-ui')].[StackName,StackStatus]" \
        --output table
}

main
