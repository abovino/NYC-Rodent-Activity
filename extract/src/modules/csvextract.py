"""
Contains a class to handle data extract from NYC Open Data API

Classes:
    Extract: Handles paginated API requests, and stages file in local tmp directory
"""
import csv
import os
from datetime import datetime, timedelta
from typing import ByteString

import boto3
from botocore.config import Config
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
    def __init__(self, query_date):
        self._write_headers = True
        self._query_date = query_date

    def __enter__(self):
        self._session = Session()
        self._file = open(f'./tmp/{self._query_date}.csv', 'w+', encoding='UTF-8')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._session.close()
        self._file.close()

    def fetch_csv_data(
        self,
        url: str,
        token: str,
        limit: int,
        offset: int,
        timeout=10,
        retries=3
    ) -> ByteString:
        """Sends GET request to download data for given date.

        Args:
            url (str): Base URL for API.
            token (str): Authentication token.
            limit (int): Max number of rows returned for each request.
            offset (int): Used to paginate the requests.
            timeout (int, optional): Time in seconds for the connection to timeout. Defaults to 10.
            retries (int, optional): Number of retry requests to attempt. Defaults to 3.

        Returns:
            ByteString: A byte string of CSV data.
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
            return response.content
        except RequestException as e:
            print(e)
            raise

    def save_csv_data(self, data: ByteString) -> int:
        """Saves CSV data to the local file system.

        Args:
            data (ByteString): ByteString containing CSV data.
            file_path (str): The path and filename to be written to.

        Returns:
            int: Number of rows in CSV file.  Used to determine offset for paginated API requests.
        """
        row_count = 0
        try:
            decoded = data.decode('UTF-8')
            writer = csv.writer(self._file, quotechar='"', quoting=csv.QUOTE_ALL)
            reader = csv.reader(decoded.splitlines(), delimiter=',', quoting=csv.QUOTE_ALL)
            field_names = next(reader, None)

            if self._write_headers:
                writer.writerow(field_names)
                self._write_headers = False

            for row in reader:
                writer.writerow(row)
                row_count += 1

            return row_count

        except FileNotFoundError as e:
            print(e)
        except IOError as e:
            print(e)

    def upload_to_s3(self, region, bucket, obj_dir):
        self._file.seek(0)
        contents = self._file.read()
        file_nm = os.path.basename(self._file.name)
        obj_key = f'{obj_dir}/{file_nm}'
        retry_strategy = {
            'total_max_attempts': 3,
            'mode': 'standard',
        }
        config = Config(
            region_name=region,
            retries=retry_strategy
        )            
        try:
            client = boto3.client('s3', config=config)
            response = client.put_object(Body=contents, Bucket=bucket, Key=obj_key)
            return response
        except Exception as e:
            print(e)
