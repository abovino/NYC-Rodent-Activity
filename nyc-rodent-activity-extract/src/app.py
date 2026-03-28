"""AWS Lambda function to get JSON data from NYC Open Data API and upload to S3 Bucket"""
import os
import json

from modules.api_extract_client import PaginatedAPIClient
from modules.s3_uploader import S3Uploader
from modules.env_variable_validation import get_required_env
from modules.query_dates import resolve_query_dates, process_date


def lambda_handler(event, context) -> dict:
    S3_DEST_BUCKET = get_required_env('S3_DEST_BUCKET')
    S3_REGION = get_required_env('S3_REGION')
    API_TOKEN = get_required_env('API_TOKEN')
    AWS_SSO_PROFILE = os.getenv('AWS_SSO_PROFILE')
    API_RESOURCE_CODE = event['API_RESOURCE_CODE']
    S3_SUB_DIR = event['S3_SUB_DIR']
    BASE_URL = f'https://data.cityofnewyork.us/resource/{API_RESOURCE_CODE}.json'

    query_dates = resolve_query_dates(event)

    uploader = S3Uploader(
        region=S3_REGION,
        bucket=S3_DEST_BUCKET,
        sub_dir=S3_SUB_DIR,
        aws_sso_profile=AWS_SSO_PROFILE,
    )

    results = []

    with PaginatedAPIClient(base_url=BASE_URL, api_token=API_TOKEN) as client:
        for query_date in query_dates:
            result = process_date(
                client=client,
                uploader=uploader,
                query_date=query_date,
            )
            results.append(result)

    return {
        "processed_dates": query_dates,
        "results": results,
    }

