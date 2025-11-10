import json
import os
import boto3
import tempfile
from huggingface_hub import HfApi, snapshot_download
from url_handler import URLHandler, URLCategory
from rds_connection import run_query

def lambda_handler(event, context):
    try:
        artifact_type = event["pathParameters"]["artifact_type"]
        body = json.loads(event.get("body", "{}"))
        url = body.get("url")

        if not url:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing url"})}

        # Step 1: Validate and classify URL
        url_handler = URLHandler()
        url_data = url_handler.handle_url(url)

        if not url_data.is_valid:
            return {"statusCode": 400, "body": json.dumps({"error": "Invalid URL"})}

        s3 = boto3.client("s3")
        bucket = os.environ["S3_BUCKET"]

        # Step 2: Ingest based on category
        if url_data.category == URLCategory.HUGGINGFACE and artifact_type == "model":
            api = HfApi()
            model_info = api.model_info(url_data.unique_identifier)
            metadata = {
                "name": model_info.modelId,
                "type": artifact_type,
                "author": model_info.author,
                "tags": model_info.tags,
                "downloads": model_info.downloads,
                "likes": model_info.likes,
            }

            # Download and upload to S3
            tmp_dir = tempfile.mkdtemp()
            snapshot_download(repo_id=url_data.unique_identifier, local_dir=tmp_dir)
            for root, _, files in os.walk(tmp_dir):
                for f in files:
                    local_path = os.path.join(root, f)
                    rel_path = os.path.relpath(local_path, tmp_dir)
                    s3.upload_file(local_path, bucket, f"models/{metadata['name']}/{rel_path}")

            download_url = f"https://{bucket}.s3.amazonaws.com/models/{metadata['name']}/"

        elif url_data.category == URLCategory.GITHUB and artifact_type == "code":
            metadata = {
                "name": url_data.repository,
                "type": artifact_type,
                "source": "github",
            }
            download_url = url  # for now, direct to GitHub

        elif url_data.category == URLCategory.NPM and artifact_type == "dataset":
            metadata = {
                "name": url_data.package_name,
                "type": artifact_type,
                "source": "npm",
            }
            download_url = url

        else:
            return {"statusCode": 400, "body": json.dumps({"error": "URL does not match artifact_type"})}

        # Step 3: Insert into DB
        query = """
        INSERT INTO artifacts (name, type, source_url, download_url)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
        """
        artifact_id = run_query(query, (metadata["name"], artifact_type, url, download_url), fetch=True)[0]["id"]

        # Step 4: Return formatted response
        response = {
            "metadata": {
                "name": metadata["name"],
                "id": artifact_id,
                "type": artifact_type
            },
            "data": {
                "url": url,
                "download_url": download_url
            }
        }

        return {"statusCode": 201, "body": json.dumps(response)}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
