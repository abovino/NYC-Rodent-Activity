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
        limit: int,
        offset: int,
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

    def save_csv_data(self, data: ByteString, file_path: str) -> int:
        """Saves CSV data to the local file system.

        Args:
            data (ByteString): ByteString containing CSV data.
            file_path (str): The path and filename to be written to.

        Returns:
            int: Number of rows in CSV file.  Used to determine offset for paginated API requests.
        """
        row_count = 0
        try:
            self._file = open(file_path, 'w', encoding='UTF-8')
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
