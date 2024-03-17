"""AWS Lambda function to get CSV data from NYC Open Data API and upload to S3 Bucket"""
import json
from typing import Dict, Any

from modules.csvextract import Extract
from modules.eventkeyvalidation import validate_keys

def extract(event, context) -> Dict[str, Any]:
    """AWS Lambda function entry point.

    Args:
        event (dict): Contains parameters for making API request.
        context (dict): Provides info about invocation, function, and execution environment

    Returns:
        Dict[str, Any]: Returns a JSON-like dict with str key and Any value.
    """
    err_response = validate_keys(event)

    if err_response:
        return err_response

    API_RESOURCE_CODE = event['API_RESOURCE_CODE']
    QUERY_DATE = event['QUERY_DATE']
    API_TOKEN = event['API_TOKEN']
    S3_BUCKET = event['S3_BUCKET']
    S3_REGION = event['S3_REGION']
    S3_OBJ_PATH = event['S3_OBJ_PATH']
    BASE_URL = f'https://data.cityofnewyork.us/resource/{API_RESOURCE_CODE}.csv?'

    with Extract(QUERY_DATE) as client:
        limit = 50000
        offset = 0
        while True:
            data = client.fetch_csv_data(BASE_URL, API_TOKEN, limit, offset)
            row_count = client.save_csv_data(data)

            if row_count < limit:
                break

            offset += limit

        s3_response = client.upload_to_s3(S3_REGION, S3_BUCKET, S3_OBJ_PATH)

        return json.dumps(s3_response)

if __name__ == '__main__':
    with open('./extract/events/env.json', 'r', encoding='UTF-8') as f:
        test_event = json.load(f)
        s3_res = extract(test_event, context={})
