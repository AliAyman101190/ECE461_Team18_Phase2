import json
from submetrics import ReviewedenessMetric

metric = ReviewedenessMetric()

import os
print("DEBUG Token (first 10 chars):", os.getenv("TEAM18_GITHUB_TOKEN")[:] if os.getenv("TEAM18_GITHUB_TOKEN") else "None")


model_info = {
    "github_repo": "https://github.com/psf/requests"
}

result = metric.calculate_metric(model_info)
print(f"Reviewedeness Score: {result:.2f}")
print(f"Latency: {metric.calculate_latency()} ms")

import requests, os
headers = {"Authorization": f"Bearer {os.getenv('TEAM18_GITHUB_TOKEN')}"}
resp = requests.get("https://api.github.com/user", headers=headers)
print(resp.status_code, resp.json().get("login"))
