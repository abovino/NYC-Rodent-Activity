## Build and Deploy AWS Lambda Function

    sam build --template path/to/template.yaml
    ...
    sam deploy --stack-name stack-name --s3-bucket dest-bucket --s3-prefix bucket/dir --capabilities CAPABILITY_IAM