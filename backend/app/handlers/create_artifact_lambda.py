import json

def lambda_handler(event, context):
    """
    Lambda function that returns all incoming request data for debugging and inspection.
    Works with AWS_PROXY integration from API Gateway.
    """

    # Log the raw event to CloudWatch
    print(json.dumps(event, indent=2))

    # Prepare response data (just return the whole event)
    response_body = {
        "message": "Request received successfully",
        "method": event.get("httpMethod"),
        "path": event.get("path"),
        "headers": event.get("headers"),
        "queryStringParameters": event.get("queryStringParameters"),
        "pathParameters": event.get("pathParameters"),
        "body": event.get("body"),
        "stageVariables": event.get("stageVariables"),
        "requestContext": event.get("requestContext"),
    }

    # Return everything in JSON
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response_body, indent=2)
    }
