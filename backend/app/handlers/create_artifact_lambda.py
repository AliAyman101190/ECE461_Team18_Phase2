import json


def lambda_handler(event, context):
    # Parse the incoming event to extract artifact details
    artifact_data = json.loads(event['body'])

    # Here you would typically add code to store the artifact in a database
    # For demonstration, we'll just return the received data

    response = {
        "statusCode": 201,
        "body": json.dumps({
            "message": "Artifact created successfully",
            "artifact": artifact_data
        }),
        "headers": {
            "Content-Type": "application/json"
        }
    }

    return response
