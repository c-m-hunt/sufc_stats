from typing import Dict
import json
from os.path import exists
import hashlib
import os

CACHE_BASE = os.getcwd()


def set_cache_base(cache_base: str):
    global CACHE_BASE
    CACHE_BASE = cache_base


def cache_request(func):
    def wrapped(url: str, params: Dict[str, str]):
        cache_key = get_cache_key(url, params)
        data = get_cache(cache_key)
        if data is None:
            data = func(url, params)
            set_cache(cache_key, data)
        return data
    return wrapped


def get_cache(cache_key: str) -> any:
    file_name = get_cache_file_name(cache_key)
    if exists(file_name):
        f = open(file_name, "r")
        data = f.read()
        f.close()
        return json.loads(data)


def set_cache(cache_key: str, data: any):
    f = open(get_cache_file_name(cache_key), "a")
    f.write(json.dumps(data))
    f.close()


def get_cache_key(url: str, params: Dict[str, str]) -> str:
    key = f"{url}-{json.dumps(params)}"
    return hashlib.md5(key.encode()).hexdigest()


def get_cache_file_name(cache_key: str) -> str:
    return f"{CACHE_BASE}/data/{cache_key}.json"
