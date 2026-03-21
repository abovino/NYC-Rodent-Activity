"""Module to validate event keys"""
import re
import json

def validate_keys(event: dict) -> dict:
    """Checks if mandatory keys exist and if QUERY_DATE is ISO format IE YYYY-MM-DD.

    Args:
        event (dict): The event dict passed to the AWS Lambda function when it's invoked.

    Returns:
        dict: Json response with err msg and HTTP status code, or empty dict if no errors.
    """
    required_keys = [
        'API_RESOURCE_CODE', 
        'QUERY_DATE', 
        'API_TOKEN',
        'S3_BUCKET',
        'S3_REGION',
        'S3_SUB_DIR',
        'AWS_SSO_PROFILE',
    ]
    for key in required_keys:
        if key not in event:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f'Missing event key: {key}'}) 
            }
    pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    match = re.match(pattern, event['QUERY_DATE'])
    if not match:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "QUERY_DATE format must be YYYY-MM-DD"}),
        }
    return {}
