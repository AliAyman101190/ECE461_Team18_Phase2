import json
import os
import boto3
import psycopg2
from urllib.parse import urlparse

from auth import require_auth
from metric_calculator import MetricCalculator
from url_handler import URLHandler
from url_category import URLCategory
from url_data import URLData
from data_retrieval import DataRetriever

S3_BUCKET = os.environ.get("S3_BUCKET")
SECRET_NAME = os.environ.get("SECRET_NAME", "DB_CREDS")

secrets_client = boto3.client("secretsmanager")
sqs_client = boto3.client("sqs")


# -----------------------------
# DB Connection Helper
# -----------------------------
def get_db_connection():
    secret_response = secrets_client.get_secret_value(SecretId=SECRET_NAME)
    creds = json.loads(secret_response["SecretString"])

    return psycopg2.connect(
        host=creds["host"],
        port=creds["port"],
        dbname=creds["dbname"],
        user=creds["username"],
        password=creds["password"],
    )


# -----------------------------
# Helper: Extract HF Identifier
# -----------------------------
def parse_huggingface_identifier(url: str):
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"   # e.g. "google-bert/bert-base-uncased"
    return None


# -----------------------------
# Lambda Handler
# -----------------------------
def lambda_handler(event, context):
    # --------------------------
    # 1. Authentication
    # --------------------------
    valid, error = require_auth(event)
    if not valid:
        return error   # already structured 403

    try:
        body = json.loads(event.get("body", "{}"))
        url = body.get("url")
        artifact_type = event.get("pathParameters", {}).get("artifact_type")

        # --------------------------
        # 2. Validate request
        # --------------------------
        if not url or not artifact_type:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing URL or artifact_type"})
            }

        identifier = parse_huggingface_identifier(url)
        if not identifier:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Invalid Hugging Face URL"})
            }

        # --------------------------
        # 3. Duplicate check
        # --------------------------
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM artifacts WHERE url = %s AND type = %s;",
            (url, artifact_type)
        )
        row = cur.fetchone()

        if row:
            cur.close()
            conn.close()
            return {
                "statusCode": 409,
                "body": json.dumps({
                    "error": "Artifact already exists",
                    "id": row[0]
                })
            }

        # --------------------------
        # 4. RATING PIPELINE
        # --------------------------
        url_handler = URLHandler()
        data_retriever = DataRetriever(
            github_token=os.environ.get("GITHUB_TOKEN"),
            hf_token=os.environ.get("HF_TOKEN")
        )
        calc = MetricCalculator()

        model_obj = URLData(url=url, category=URLCategory.HUGGINGFACE, is_valid=True)

        # get metadata from HF repo (README, config, tags, etc)
        repo_data = data_retriever.retrieve_data(model_obj)

        model_dict = {
            **repo_data.__dict__,
            "name": identifier
        }

        rating = calc.calculate_all_metrics(model_dict, category="MODEL")
        net_score = rating["net_score"]

        # --------------------------
        # 5. Reject if disqualified
        # --------------------------
        if net_score < 0.5:
            # insert into DB as disqualified (spec requires this)
            cur.execute(
                """
                INSERT INTO artifacts (type, url, name, net_score, ratings, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
                """,
                (artifact_type, url, identifier, net_score, json.dumps(rating), "disqualified")
            )
            artifact_id = cur.fetchone()[0]
            conn.commit()

            cur.close()
            conn.close()

            return {
                "statusCode": 424,  # FAILED_DEPENDENCY
                "body": json.dumps({
                    "error": "Artifact disqualified by rating",
                    "net_score": net_score,
                    "id": artifact_id
                })
            }

        # --------------------------
        # 6. Insert as upload_pending
        # --------------------------
        cur.execute(
            """
            INSERT INTO artifacts (type, url, name, net_score, ratings, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """,
            (artifact_type, url, identifier, net_score, json.dumps(rating), "upload_pending")
        )

        artifact_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()

        # --------------------------
        # 7. Send SQS message to ECS ingest worker
        # --------------------------
        sqs_client.send_message(
            QueueUrl=os.environ.get("INGEST_QUEUE_URL"),
            MessageBody=json.dumps({
                "artifact_id": artifact_id,
                "artifact_type": artifact_type,
                "identifier": identifier,
                "source_url": url
            })
        )

        # --------------------------
        # 8. SUCCESS (201)
        # --------------------------
        return {
            "statusCode": 201,
            "body": json.dumps({
                "metadata": {
                    "name": identifier,
                    "id": artifact_id,
                    "type": artifact_type
                },
                "data": {
                    "url": url
                }
            })
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
