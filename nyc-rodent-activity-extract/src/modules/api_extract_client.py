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
        headers = {"X-App-Token": self._api_token}
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
            query_date (str): Date in YYYY-MM-DD format.
            limit (int): Max number of rows returned for each request.
            offset (int): Used to paginate the requests.
            timeout (int, optional): Time in seconds for the connection to timeout.

        Returns:
            list[dict[str, Any]]: Parsed JSON response.
        """
        where = self._build_query_where_clause(query_date)
        params = {
            "$where": where,
            "$limit": limit,
            "$offset": offset,
            "$order": ":id",
            "$$exclude_system_fields": "false",
        }
        try:
            response = self._session.get(
                self._base_url,
                params=params,
                timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            raise RuntimeError(f"Failed to fetch data from {self._base_url}") from e
        

    def _build_query_where_clause(self, query_date: str) -> str:
        start_dt = datetime.strptime(query_date, "%Y-%m-%d")
        end_dt = start_dt + timedelta(days=1)

        start_ts = start_dt.strftime("%Y-%m-%dT00:00:00")
        end_ts = end_dt.strftime("%Y-%m-%dT00:00:00")

        where_clause = (
            f"(:created_at >= '{start_ts}' AND :created_at < '{end_ts}') "
            f"OR "
            f"(:updated_at >= '{start_ts}' AND :updated_at < '{end_ts}')"
        )

        return where_clause

