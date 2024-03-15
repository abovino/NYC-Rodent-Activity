import json

def extract(event, context):
    message = event['msg']
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Your message: {message}'
        })
    }

if __name__ == '__main__':
    with open('./extract/events/event.json', 'r', encoding='UTF-8') as f:
        test_event = json.load(f)
        s3_res = extract(test_event, context={})
        status_code = s3_res['statusCode']
        msg = json.loads(s3_res['body'])['message']
        print(f"HTTPStatus: {status_code}, {msg}")
