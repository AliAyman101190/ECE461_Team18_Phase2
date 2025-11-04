import json
from datetime import datetime

def lambda_handler(event, context):
    # Simulated data
    fake_models = [
        {
            "id": "bert-001",
            "name": "bert-base-cased",
            "submittedBy": "Ali",
            "status": "Ingested",
            "dateAdded": datetime.utcnow().isoformat() + "Z"
        },
        {
            "id": "gpt2-002",
            "name": "gpt2-small",
            "submittedBy": "John",
            "status": "Pending",
            "dateAdded": datetime.utcnow().isoformat() + "Z"
        },
        {
            "id": "falcon-003",
            "name": "falcon-7b-instruct",
            "submittedBy": "Abdul",
            "status": "Ingested",
            "dateAdded": datetime.utcnow().isoformat() + "Z"
        }
    ]

    # Standard API Gateway–style response
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(fake_models)
    }
