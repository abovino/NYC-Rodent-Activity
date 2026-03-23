from datetime import datetime, timedelta
from api_extract_client import PaginatedAPIClient
from s3_uploader import S3Uploader

def resolve_query_dates(event: dict) -> list[str]:
    if "START_DATE" in event and "END_DATE" in event:
        start_date = datetime.strptime(event["START_DATE"], "%Y-%m-%d").date()
        end_date = datetime.strptime(event["END_DATE"], "%Y-%m-%d").date()

        if start_date >= end_date:
            raise ValueError("START_DATE must less than END_DATE")
        

        max_days = 15
        day_count = (end_date - start_date).days + 1

        if day_count > max_days:
            raise ValueError(f"Date range cannot exceed {max_days} days")
        

        query_dates = []

        for i in range(day_count):
            query_dates.append((start_date + timedelta(days=i)).isoformat())

        return query_dates
    

    if "QUERY_DATE" in event:
        datetime.strptime(event["QUERY_DATE"], "%Y-%m-%d")
        return [event["QUERY_DATE"]]
    

    raise ValueError("Event must include QUERY_DATE or START_DATE and END_DATE")


def process_date(client: PaginatedAPIClient, uploader: S3Uploader, query_date: str) -> dict:
    limit = 50000
    offset = 0
    files_uploaded = 0
    total_records = 0
    uploads = []

    while True:
        data = client.get_json_batch(query_date, limit, offset)

        if not data:
            break
        
        response = uploader.upload_json(data, query_date)
        uploads.append(response)

        record_count = len(data)
        total_records += record_count
        files_uploaded += 1

        if record_count < limit:
            break

        offset += limit

    if files_uploaded == 0:
        raise ValueError(f"API returned no data for {query_date}")
    
    return {
        "query_date": query_date,
        "files_uploaded": files_uploaded,
        "total_records": total_records,
        "uploads": uploads,
    }