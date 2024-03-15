import json

from modules.csvextract import Extract

def extract(event, context):
    API_RESOURCE_CODE = event['API_RESOURCE_CODE']
    QUERY_DATE = event['QUERY_DATE']
    API_TOKEN = event['API_TOKEN']
    BASE_URL = f'https://data.cityofnewyork.us/resource/{API_RESOURCE_CODE}.csv?'
    with Extract() as client:
        data = client.fetch_csv_data(BASE_URL, API_TOKEN, QUERY_DATE)

    return data

if __name__ == '__main__':
    with open('./extract/events/env.json', 'r', encoding='UTF-8') as f:
        test_event = json.load(f)
        s3_res = extract(test_event, context={})
