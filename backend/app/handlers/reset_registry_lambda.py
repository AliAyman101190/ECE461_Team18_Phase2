import json
from rds_connection import run_query

def lambda_handler(event, context):
    try:
        # Delete all artifacts
        run_query("DELETE FROM artifacts;")

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Registry reset successfully!"})
        }

    except Exception as e:
        print("❌ Error:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
