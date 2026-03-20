"""
Classes:
    S3Uploader: Uploads JSON data to partitioned S3 bucket
"""
import json
import boto3
from datetime import datetime, timezone, timedelta
from typing import Any
from botocore.config import Config
from botocore.exceptions import ClientError

class S3Uploader:
    def __init__(self,
        region: str,
        bucket: str,
        sub_dir: str,
        aws_sso_profile: str,
    ) -> None:
        self._region = region
        self._bucket = bucket
        self._sub_dir = sub_dir
        self._aws_sso_profile = aws_sso_profile

    def upload_json(self, data: list[dict], query_date: str) -> dict:
        """Uploads JSON data to S3 bucket.

        Args:
            data (list[dict[str, Any]]): API JSON response
            region (str): AWS region for S3 bucket.
            bucket (str): S3 bucket upload destination.
            sub_dir (str): S3 bucket sub directory for upload
            aws_sso_profile (str): SSO Profile to use for Boto3 authentication

        Returns:
            dict: Contains respose data from S3, or error data in JSON format
        """
        retry_strategy = {'total_max_attempts': 3, 'mode': 'standard'}
        config = Config(region_name=self._region, retries=retry_strategy)
        json_bytes = json.dumps(data).encode("utf-8")
        obj_key = self._create_partitioned_obj_key(query_date)

        try:
            session = boto3.Session(profile_name=self._aws_sso_profile)
            client = session.client('s3', config=config)
            response = client.put_object(
                Body=json_bytes,
                Bucket=self._bucket,
                Key=obj_key,
                ContentType="application/json"
            )
            status_code = response['ResponseMetadata']['HTTPStatusCode']
            response_body = {'message': 'Files uploaded successfully'}
            response = self._format_lambda_response(status_code, response_body)
            return response
        
        except ClientError as e:
            status_code = e.response['ResponseMetadata']['HTTPStatusCode']
            response_body = {'error': e.response['Error']['Message']}
            err_response = self._format_lambda_response(status_code, response_body)
            return err_response
        return
    

    def _create_partitioned_obj_key(self, query_date: str) -> str:
        """Generates a paritioned path for S3 file upload.

        Args:
            query_date (str)

        Returns:
            str: partitioned S3 path
        """
        upload_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        file_nm = f"{self._sub_dir}_extract_{query_date}_upload_{upload_date}.json"
        year, month, day = query_date.split('-')
        obj_key = f"{self._sub_dir}/raw/year={year}/month={month}/day={day}/{file_nm}"
        return obj_key
    

    def _format_lambda_response(self, status_code: int, body: dict) -> dict:
        """Formats the response for the AWS Lambda Function.

        Args:
            status_code (int): Status code to send to the client.
            body (dict): Response body to send to the client.

        Returns:
            dict: HTTP status code, headers, and body
        """
        res = {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json',
            },
            'body': body
        }
        return res