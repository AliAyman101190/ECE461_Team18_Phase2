import json
from rds_connection import run_query

def lambda_handler(event, context):
    """Delete an artifact by its ID and type from the database."""

    print("Incoming event:", json.dumps(event, indent=2))

    # --- Extract path parameters from the API Gateway event ---
    path_params = event.get("pathParameters") or {}
    artifact_type = path_params.get("artifact_type")
    artifact_id = path_params.get("id")

    # --- Validate input ---
    if not artifact_type or not artifact_id:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing artifact_type or id in path"})
        }

    # --- Run delete query ---
    try:
        sql = "DELETE FROM artifacts WHERE id = %s AND type = %s RETURNING id;"
        result = run_query(sql, (artifact_id, artifact_type), fetch=True)

        if not result:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Artifact not found"})
            }

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Artifact deleted", "deleted_id": artifact_id})
        }

    except Exception as e:
        print("❌ Error deleting artifact:", e)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
