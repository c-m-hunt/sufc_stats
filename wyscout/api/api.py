import base64
import os
from typing import Dict

import requests

BASE_URL = "https://apirest.wyscout.com/v4/"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")


def get_request(url: str, params: Dict[str, str]) -> any:
    url = BASE_URL + url
    auth_bytes = f"{CLIENT_ID}:{CLIENT_SECRET}".encode("ascii")
    base64_bytes = base64.b64encode(auth_bytes)
    base64_auth = base64_bytes.decode("ascii")
    headers = {"Authorization": f"Basic {base64_auth}"}
    response = requests.get(url, params=params, headers=headers, timeout=10)
    return response.json()
