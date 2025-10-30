import json

def lambda_handler(event, context):
    print(json.dumps(event))  # logs to CloudWatch
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "message": f"{event['resource']} called successfully from Github actions 2",
            "method": event['httpMethod'],
            "pathParameters": event.get('pathParameters'),
            "query": event.get('queryStringParameters'),
        })
    }
