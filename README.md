## Build and Deploy AWS Lambda Function

    sam build --template path/to/template.yaml
    ...
    sam deploy --stack-name stack-name \
    --s3-bucket dest-bucket \
    --s3-prefix bucket/dir \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides S3DestBucket=bucket-name

    aws lambda invoke --function-name <lambda-func-name> --payload fileb://path/to/payload.json response.json

    ToDo:
        - Make the Lambda function/API requests more dynamic so a date range can be passed
        - Handle status_code/response_body in S3Uploader.upload_json()