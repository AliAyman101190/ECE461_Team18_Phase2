import json
import os
import boto3
import psycopg2
import urllib.request
from urllib.parse import urlparse

S3_BUCKET = os.environ.get("S3_BUCKET")
SECRET_NAME = os.environ.get("SECRET_NAME", "DB_CREDS")

secrets_client = boto3.client("secretsmanager")
s3_client = boto3.client("s3")


def get_db_connection():
    """Retrieve DB credentials from Secrets Manager and connect to Postgres."""
    secret_response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
    secret = json.loads(secret_response["SecretString"])
    return psycopg2.connect(
        host=secret["host"],
        port=secret["port"],
        dbname=secret["dbname"],
        user=secret["username"],
        password=secret["password"],
    )


def parse_huggingface_url(url: str):
    """Extract model identifier from Hugging Face URL."""
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return None


def list_huggingface_files(identifier: str):
    """Return list of file paths for a Hugging Face model."""
    api_url = f"https://huggingface.co/api/models/{identifier}"
    with urllib.request.urlopen(api_url) as response:
        data = json.load(response)
        siblings = data.get("siblings", [])
        return [file["rfilename"] for file in siblings]


def download_and_upload_to_s3(identifier: str, artifact_type: str, artifact_id: int):
    """Stream all model files from HF → directly to S3."""
    files = list_huggingface_files(identifier)
    for filename in files:
        hf_file_url = f"https://huggingface.co/{identifier}/resolve/main/{filename}"
        s3_key = f"{artifact_type}/{artifact_id}/{filename}"
        try:
            with urllib.request.urlopen(hf_file_url) as response:
                s3_client.upload_fileobj(response, S3_BUCKET, s3_key)
        except Exception as e:
            print(f"Failed to upload {filename}: {e}")


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        url = body.get("url")
        artifact_type = event.get("pathParameters", {}).get("artifact_type")

        if not url or not artifact_type:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing URL or artifact_type"})
            }

        identifier = parse_huggingface_url(url)
        if not identifier:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid Hugging Face URL"})
            }

        # --- Insert DB record ---
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO artifacts (type, url, name) VALUES (%s, %s, %s) RETURNING id;",
            (artifact_type, url, identifier),
        )
        artifact_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        # --- Download all files to S3 ---
        download_and_upload_to_s3(identifier, artifact_type, artifact_id)

        return {
            "statusCode": 201,
            "body": json.dumps({
                "message": f"Artifact '{identifier}' ingested successfully",
                "artifact": {
                    "id": artifact_id,
                    "type": artifact_type,
                    "identifier": identifier,
                    "s3_prefix": f"s3://{S3_BUCKET}/{artifact_type}/{artifact_id}/"
                }
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
