import base64
import os

import requests

BASE_URL = "https://apirest.wyscout.com/v4/"
TIMEOUT_SECONDS = 30


def _auth_header() -> dict[str, str]:
    # read at call time, so a .env loaded after import is still picked up
    client_id = os.getenv("CLIENT_ID", "")
    client_secret = os.getenv("CLIENT_SECRET", "")
    token = base64.b64encode(f"{client_id}:{client_secret}".encode("ascii")).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def get_request(url: str, params: dict[str, str]) -> any:
    response = requests.get(
        BASE_URL + url, params=params, headers=_auth_header(), timeout=TIMEOUT_SECONDS
    )
    return response.json()
