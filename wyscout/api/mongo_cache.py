import datetime
import hashlib
import json
import os
from typing import Dict

from pymongo import MongoClient

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")

client = MongoClient(MONGO_HOST, 27017)
db = client.wyscout


def get_cache(collection: str, cache_key: str) -> any:
    rec = db[collection].find_one({"key": cache_key})
    if rec is not None:
        if rec["expires"] < datetime.datetime.utcnow():
            db[collection].delete_one({"_id": rec["_id"]})
            return None
        else:
            return rec["data"]
    return None


def set_cache(collection: str, cache_key: str, data: any, expires_hr: int):
    db[collection].insert_one(
        {
            "key": cache_key,
            "data": data,
            "expires": datetime.datetime.utcnow()
            + datetime.timedelta(hours=expires_hr),
        }
    )


def get_cache_key(args: Dict) -> str:
    key = json.dumps(args)
    return hashlib.md5(key.encode()).hexdigest()


def cache_request(collection: str, expires_hr: int = 72):
    def decorator(func):
        def wrapped(*args, **kwargs):
            cache_key = get_cache_key(
                {"args": locals()["args"], "kwargs": locals()["kwargs"]}
            )
            data = get_cache(collection, cache_key)
            if data is None:
                data = func(*args, **kwargs)
                set_cache(collection, cache_key, data, expires_hr)
            return data

        return wrapped

    return decorator
