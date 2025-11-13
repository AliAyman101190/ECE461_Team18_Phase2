FROM public.ecr.aws/lambda/python:3.11

# Install system deps (psycopg2 needs libpq)
RUN yum -y install postgresql-libs && yum clean all

# Copy worker code
WORKDIR /var/task
COPY ingest_worker.py .
COPY requirements.txt .

# Install Python deps
RUN pip install --no-cache-dir -r requirements.txt

# Set the handler (for Lambda-style image), but we'll just run as a normal process
CMD ["ingest_worker.main_loop"]
