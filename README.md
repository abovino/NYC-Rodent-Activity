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

## Local testing
    - Setup venv
        - python -m venv .venv
    - Activate venv
        - cmd .venv\Scripts\activate.bat
        - linux source .venv/bin/activate
        - git bash source .venv/Scripts/activate
    - Setup environment variables
        - S3_DEST_BUCKET
        - S3_REGION
        - AWS_SSO_PROFILE
    - Run locally
        - $ python \
            nyc-rodent-activity-extract/run_local.py \
            nyc-rodent-activity-extract/events/your_test_event.json
    

    ToDo:
        - Make the Lambda function/API requests more dynamic so a date range can be passed
        - Add src/run_local.py 