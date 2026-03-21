## Build and Deploy AWS Lambda Function

    sam build --template path/to/template.yaml
    ...
    sam deploy \
    --provile sso-profile
    --stack-name stack-name \
    --resolve-s3 \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides \
    S3DestBucket=bucket-name \
    S3Region=s3-region

    aws lambda invoke --function-name <lambda-func-name> --payload fileb://path/to/payload.json response.json

    ToDo:
        - Make the Lambda function/API requests more dynamic so a date range can be passed