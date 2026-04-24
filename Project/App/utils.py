import requests
from django.conf import settings

def run_code(code, stdin):
    url = "https://api.jdoodle.com/v1/execute"

    payload = {
        "clientId": settings.JDOODLE_CLIENT_ID,
        "clientSecret": settings.JDOODLE_CLIENT_SECRET,
        "script": code,
        "language": "python3",
        "versionIndex": "4",
        "stdin": stdin
    }

    response = requests.post(url, json=payload)
    return response.json()
