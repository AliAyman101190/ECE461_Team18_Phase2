import json
import os
import boto3
from url_handler import URLHandler
from data_retrieval import DataRetriever
from rds_connection import run_query

def lambda_handler(event, context):
    try:
        artifact_type = event["pathParameters"]["artifact_type"]
        body = json.loads(event.get("body", "{}"))
        url = body.get("url")

        if not url:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing URL"})}

        # 1️⃣ Parse and classify URL
        handler = URLHandler()
        url_data = handler.handle_url(url)
        if not url_data or not url_data.is_valid:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid URL format"})}

        # 2️⃣ Fetch metadata via DataRetriever
        retriever = DataRetriever(
            github_token=os.getenv("GITHUB_TOKEN"),
            hf_token=os.getenv("HF_TOKEN")
        )
        repo_data = retriever.retrieve_data(url_data)

        if not repo_data.success:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": repo_data.error_message or "Failed to retrieve artifact data"})
            }

        # 3️⃣ Upload to S3 (optional first — you can skip large files initially)
        s3 = boto3.client("s3")
        bucket = os.environ["S3_BUCKET"]

        folder_name = f"{artifact_type}s/{repo_data.name}"
        s3_path = f"https://{bucket}.s3.amazonaws.com/{folder_name}/"
        # Optional: upload README or minimal metadata
        if repo_data.readme:
            s3.put_object(
                Bucket=bucket,
                Key=f"{folder_name}/README.md",
                Body=repo_data.readme.encode("utf-8"),
                ContentType="text/markdown"
            )

        # 4️⃣ Store metadata in RDS
        query = """
        INSERT INTO artifacts (name, type, source_url, download_url, metadata)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        metadata_json = json.dumps(repo_data.__dict__, default=str)
        result = run_query(
            query,
            (repo_data.name, artifact_type, url, s3_path, metadata_json),
            fetch=True
        )
        artifact_id = result[0]["id"]

        # 5️⃣ Return spec-compliant response
        response = {
            "metadata": {
                "name": repo_data.name,
                "id": artifact_id,
                "type": artifact_type
            },
            "data": {
                "url": url,
                "download_url": s3_path
            }
        }

        return {"statusCode": 201, "body": json.dumps(response)}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
