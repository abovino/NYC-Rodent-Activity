import csv
from datetime import datetime, timedelta
from typing import ByteString

from requests import Session
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import RequestException


class Extract:
    def __init__(self):
        self._write_headers = True
        self._file = None

    def __enter__(self):
        self.session = Session()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.session.close()
        if self._file:
            self._file.close()

    def fetch_csv_data(
        self,
        url: str,
        token: str,
        date: str,
        limit=50000,
        offset=0,
        timeout=10,
        retries=3
    ) -> ByteString:
        cols = '*,:id,:created_at,:updated_at,:version'
        headers = {'X-App-Token': token}
        start = date
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
        self.session.mount('https://', api_adapter)
        try:
            response = self.session.get(url, params=params, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response.content
        except RequestException as e:
            print(e)
            raise
