"""
Classes:
    ExtPaginatedAPIClientract: Creates a session for paginated API requests
"""
from datetime import datetime, timedelta
from typing import Any
from requests import Session
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import RequestException

class PaginatedAPIClient:
    """Handles paginated API requests"""
    def __init__(self, base_url: str, api_token: str) -> None:
        self._base_url = base_url
        self._api_token = api_token
        

    def __enter__(self):
        headers = {'X-App-Token': self._api_token}
        self._retry_strategy = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist={408, 502, 503, 504},
            raise_on_status=False
        )
        self._api_adapter = HTTPAdapter(max_retries=self._retry_strategy)
        self._session = Session()
        self._session.mount('https://', self._api_adapter)
        self._session.headers.update(headers)
        return self


    def __exit__(self, exc_type, exc_value, traceback):
        if self._session:
            self._session.close()

    
    def get_json_batch(self, query_date: str, limit: int, offset: int, timeout=10) -> list[dict[str, Any]]:
        """Sends GET request to download data for given date.

        Args:
            limit (int): Max number of rows returned for each request.
            offset (int): Used to paginate the requests.
            timeout (int, optional): Time in seconds for the connection to timeout. Defaults to 10.

        Returns:
            list[dict[str, Any]]: A JSONified list.
        """
        cols = '*,:id,:created_at,:updated_at,:version'
        start = query_date
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
        try:
            response = self._session.get(self._base_url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise RuntimeError(f"Failed to fetch data from {self._base_url}") from e