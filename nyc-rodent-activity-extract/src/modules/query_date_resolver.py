from datetime import datetime, timedelta


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

