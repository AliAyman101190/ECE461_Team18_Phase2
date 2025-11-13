FROM python:3.11-slim

WORKDIR /app

RUN pip install boto3

COPY worker.py .

CMD ["python", "worker.py"]
