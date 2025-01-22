echo "=== CloudFront Status ===" && aws cloudfront get-distribution --id E2NGSO7RCE1JO3 --query "Distribution.Status" && echo -e "
=== S3 Content ===" && aws s3 ls s3://test-warehouse-ui-content-test-202501221845 --human-readable --summarize && echo -e "
=== WAF Rules ===" && aws wafv2 list-web-acls --scope CLOUDFRONT --region us-east-1 --query "WebACLs[?contains(Name, \`test-warehouse-ui\`)].Name" --output table && echo -e "
=== CloudFront Cache Stats ===" && aws cloudfront get-distribution --id E2NGSO7RCE1JO3 --query "Distribution.DistributionConfig.DefaultCacheBehavior.MinTTL"
