aws s3 cp $1 s3://test-warehouse-ui-content-test-202501221845/ --content-type text/html --cache-control "max-age=3600" && aws cloudfront create-invalidation --distribution-id E2NGSO7RCE1JO3 --paths "/*"
