"""AWS Lambda function to get CSV data from NYC Open Data API and upload to S3 Bucket"""
import os
import json

from modules.api_extract_client import PaginatedAPIClient
from modules.s3_uploader import S3Uploader
from modules.env_variable_validation import get_required_env
from modules.event_key_validation import validate_event_keys


def lambda_handler(event, context) -> dict:
    S3_DEST_BUCKET = get_required_env('S3_DEST_BUCKET')
    S3_REGION = get_required_env('S3_REGION')
    AWS_SSO_PROFILE = os.getenv('AWS_SSO_PROFILE')
    
    err_response = validate_event_keys(event)

    if err_response:
        return err_response
    

    API_RESOURCE_CODE = event['API_RESOURCE_CODE']
    QUERY_DATE = event['QUERY_DATE']
    API_TOKEN = event['API_TOKEN']
    S3_SUB_DIR = event['S3_SUB_DIR']
    BASE_URL = f'https://data.cityofnewyork.us/resource/{API_RESOURCE_CODE}.json?'

    uploader = S3Uploader(
        region=S3_REGION,
        bucket=S3_DEST_BUCKET,
        sub_dir=S3_SUB_DIR,
        aws_sso_profile=AWS_SSO_PROFILE,
    )

    files_uploaded = 0
    last_s3_response = None

    with PaginatedAPIClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        limit = 50000
        offset = 0

        while True:
            data = client.get_json_batch(QUERY_DATE, limit, offset)

            if not data:
                break

            last_s3_response = uploader.upload_json(data, QUERY_DATE)
            files_uploaded += 1
            record_count = len(data)

            if record_count < limit:
                break

            offset += limit
        
        if files_uploaded == 0:
            raise ValueError("API returned no data")
        
        return last_s3_response
