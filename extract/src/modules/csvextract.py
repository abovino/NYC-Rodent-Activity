"""
Contains a class to handle data extract from NYC Open Data API

Classes:
    Extract: Handles paginated API requests, and stages file in local tmp directory
"""
import csv
import os
import json
from datetime import datetime, timedelta
from typing import Any

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from requests import Session
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import RequestException


class Extract:
    """Handles paginated API requests, and stages file in local tmp directory

    Attributes:
        _write_headers (bool): If the CSV headers should be written to the file.
        _query_date (str): Date to request data for.  ISO Format YYYY-MM-DD.
        _session (Session): Persists the connection to the API
        _file (IO[str]): Open file for writing
    """
    def __init__(self, query_date, tmp_dir):
        self._write_headers = True
        self._query_date = query_date
        self._tmp_dir = tmp_dir
        self._tmp_output = os.path.join(self._tmp_dir, f'{self._query_date}.json')

    def __enter__(self):
        self._session = Session()
        self._file = open(self._tmp_output, 'w+', encoding='UTF-8')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._session.close()
        self._file.close()

    
    def get_json(self, url: str, token: str, limit: int, offset: int, timeout=10, retries=3) -> list[dict[str, Any]]:
        """Sends GET request to download data for given date.

        Args:
            url (str): Base URL for API.
            token (str): Authentication token.
            limit (int): Max number of rows returned for each request.
            offset (int): Used to paginate the requests.
            timeout (int, optional): Time in seconds for the connection to timeout. Defaults to 10.
            retries (int, optional): Number of retry requests to attempt. Defaults to 3.

        Returns:
            list[dict[str, Any]]: A JSONified list.
        """
        cols = '*,:id,:created_at,:updated_at,:version'
        headers = {'X-App-Token': token}
        start = self._query_date
        end = (datetime.strptime(start, '%Y-%m-%d')
            + timedelta(days=1)).strftime('%Y-%m-%d')
        where = (
            f":created_at BETWEEN '{start}' AND '{end}' "
            f"OR :updated_at BETWEEN '{start}' AND '{end}'"
        )
        params = {
            '$select': cols,
            '$where': where,
            '$limit': limit,
            '$offset': offset,
            '$order': ':id'
        }
        retry_codes = [408, 502, 503, 504]
        retry_strategy = Retry(
            total=retries,
            backoff_factor=1.0,
            status_forcelist=retry_codes,
            raise_on_status=False
        )
        api_adapter = HTTPAdapter(max_retries=retry_strategy)
        self._session.mount('https://', api_adapter)
        try:
            response = self._session.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise RuntimeError(f"Failed to fetch data from {url}") from e


    def upload_to_s3(self, data: list[dict[str, Any]], region: str, bucket: str, sub_dir: str, aws_sso_profile: str) -> dict:
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
        json_bytes = json.dumps(data).encode("utf-8")
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        file_nm = sub_dir + '_' + timestamp + os.path.basename(self._file.name)
        obj_key = self._generate_partitioned_path(sub_dir, file_nm)
        retry_strategy = {'total_max_attempts': 3, 'mode': 'standard'}
        config = Config(region_name=region, retries=retry_strategy)

        try:
            session = boto3.Session(profile_name="dev")
            client = session.client('s3', config=config)
            response = client.put_object(Body=json_bytes, Bucket=bucket, Key=obj_key, ContentType="application/json")
            status_code = response['ResponseMetadata']['HTTPStatusCode']
            response_body = {'message': 'File uploaded successfully'}
            response = self._format_lambda_response(status_code, response_body)
            return response
        
        except ClientError as e:
            status_code = e.response['ResponseMetadata']['HTTPStatusCode']
            response_body = {'error': e.response['Error']['Message']}
            err_response = self._format_lambda_response(status_code, response_body)
            return err_response

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

    def _generate_partitioned_path(self, sub_dir: str, file_nm: str) -> str:
        """Generates a year=YYYY/month=MM/day=DD paritioned path for S3 file upload.

        Args:
            sub_dir (str): Sub directory of S3 bucket to save paritioned file.
            file_nm (str): name of file to be uploaded to S3.

        Returns:
            str: partitioned S3 path
        """
        year, month, day = self._query_date.split('-')
        obj_key_path = (
            f"{sub_dir}/raw/year={year}/month={month}/day={day}/{file_nm}"
        )
        return obj_key_path
