"""
Classes:
    S3Uploader: Uploads JSON data to partitioned S3 bucket
"""
import json
import boto3
from datetime import datetime, timezone
from typing import Any
from botocore.config import Config
from botocore.exceptions import ClientError

class S3Uploader:
    def __init__(self,
        region: str,
        bucket: str,
        sub_dir: str,
        aws_sso_profile: str | None = None,
    ) -> None:
        self._region = region
        self._bucket = bucket
        self._sub_dir = sub_dir

        retry_strategy = {"total_max_attempts": 3, "mode": "standard"}
        config = Config(region_name=self._region, retries=retry_strategy)

        if aws_sso_profile:
            session = boto3.Session(profile_name=aws_sso_profile)
            self._client = session.client("s3", config=config)
        else:
            self._client = boto3.client("s3", config=config)
    

    def upload_json(self, data: list[dict], query_date: str) -> dict:
        """Uploads JSON data to S3 bucket.

        Args:
            data (list[dict]): API JSON response
            query_date (str)

        Returns:
            dict: Contains response data from S3
        """
        json_bytes = json.dumps(data).encode("utf-8")
        obj_key = self._create_partitioned_obj_key(query_date)

        try:
            response = self._client.put_object(
                Body=json_bytes,
                Bucket=self._bucket,
                Key=obj_key,
                ContentType="application/json",
            )
        except ClientError as e:
            message = e.response["Error"]["Message"]
            raise RuntimeError(
                f"Failed to upload s3://{self._bucket}/{obj_key}: {message}"
            ) from e

        return {
            "bucket": self._bucket,
            "key": obj_key,
            "status_code": response["ResponseMetadata"]["HTTPStatusCode"],
            "record_count": len(data),
        }
    

    def _create_partitioned_obj_key(self, query_date: str) -> str:
        """Generates a paritioned path for S3 file upload.

        Args:
            query_date (str)

        Returns:
            str: partitioned S3 path
        """
        upload_date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        file_nm = f"{self._sub_dir}_extract_{query_date}_upload_{upload_date}.json"
        dt = datetime.strptime(query_date, "%Y-%m-%d")
        year = dt.strftime("%Y")
        month = dt.strftime("%m")
        day = dt.strftime("%d")
        obj_key = f"{self._sub_dir}/raw/year={year}/month={month}/day={day}/{file_nm}"
        return obj_key
