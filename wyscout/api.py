from typing import Dict
import os
import requests
import base64
import json
from os.path import exists
import hashlib


BASE_URL = "https://apirest.wyscout.com/v3/"
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CACHE_BASE = os.getcwd()


def set_cache_base(cache_base: str):
    global CACHE_BASE
    CACHE_BASE = cache_base


def set_auth(client_id: str, client_secret: str):
    global CLIENT_ID
    global CLIENT_SECRET
    CLIENT_ID = client_id
    CLIENT_SECRET = client_secret


def get_cache_key(url: str, params: Dict[str, str]) -> str:
    key = f"{url}-{json.dumps(params)}"
    return hashlib.md5(key.encode()).hexdigest()


def set_cache(cache_key: str, data: any):
    f = open(get_cache_file_name(cache_key), "a")
    f.write(json.dumps(data))
    f.close()


def get_cache(cache_key: str) -> any:
    file_name = get_cache_file_name(cache_key)
    if exists(file_name):
        f = open(file_name, "r")
        data = f.read()
        f.close()
        return json.loads(data)


def get_cache_file_name(cache_key: str) -> str:
    return f"{CACHE_BASE}/data/{cache_key}.json"


def cache_request(func):
    def wrapped(url: str, params: Dict[str, str]):
        cache_key = get_cache_key(url, params)
        data = get_cache(cache_key)
        if data is None:
            data = func(url, params)
            set_cache(cache_key, data)
        return data
    return wrapped


@cache_request
def get_request(url: str, params: Dict[str, str]) -> any:
    url = BASE_URL + url
    auth_bytes = f"{CLIENT_ID}:{CLIENT_SECRET}".encode('ascii')
    base64_bytes = base64.b64encode(auth_bytes)
    base64_auth = base64_bytes.decode('ascii')
    headers = {"Authorization": f"Basic {base64_auth}"}
    response = requests.get(
        url, params=params, headers=headers, timeout=10)
    return response.json()
