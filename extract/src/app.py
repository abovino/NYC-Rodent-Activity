import json

from modules.csvextract import Extract
from modules.eventkeyvalidation import validate_keys

def extract(event, context):
    err_response = validate_keys(event)

    if err_response:
        return err_response

    API_RESOURCE_CODE = event['API_RESOURCE_CODE']
    QUERY_DATE = event['QUERY_DATE']
    API_TOKEN = event['API_TOKEN']
    BASE_URL = f'https://data.cityofnewyork.us/resource/{API_RESOURCE_CODE}.csv?'
    with Extract() as client:
        limit = 50000
        offset = 0
        while True:
            data = client.fetch_csv_data(BASE_URL, API_TOKEN, QUERY_DATE, limit, offset)
            row_count = client.save_csv_data(data, f'./tmp/{QUERY_DATE}.csv')

            if row_count < limit:
                break

            offset += limit

    return data

if __name__ == '__main__':
    with open('./extract/events/env.json', 'r', encoding='UTF-8') as f:
        test_event = json.load(f)
        s3_res = extract(test_event, context={})
