import json
from rds_connection import run_query

def lambda_handler(event, context):
    try:
        # Parse input body
        body = json.loads(event.get("body", "{}"))
        artifact_type = event["pathParameters"]["artifact_type"]
        url = body.get("url")

        if not url:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing 'url' in request body"})
            }

        # Insert into database
        query = """
        INSERT INTO artifacts (type, url)
        VALUES (%s, %s)
        RETURNING id, type, url, created_at;
        """
        result = run_query(query, (artifact_type, url), fetch=True)[0]

        return {
            "statusCode": 201,
            "body": json.dumps({
                "message": "Artifact created successfully!",
                "artifact": result
            })
        }

    except Exception as e:
        print("❌ Error:", str(e))
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
