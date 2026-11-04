import datetime
import hashlib
import json
import os

from pymongo import MongoClient

MONGO_HOST = os.getenv("MONGO_HOST", "localhost")

client = MongoClient(MONGO_HOST, 27017)
db = client.wyscout

_indexed_collections: set = set()


def _ensure_index(collection: str):
    if collection not in _indexed_collections:
        db[collection].create_index("key", unique=True, background=True)
        _indexed_collections.add(collection)


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
    _ensure_index(collection)
    db[collection].update_one(
        {"key": cache_key},
        {
            "$set": {
                "data": data,
                "expires": datetime.datetime.utcnow()
                + datetime.timedelta(hours=expires_hr),
            }
        },
        upsert=True,
    )

def is_error_response(data: any) -> bool:
    # an error, or the bare {"message": ...} the API sends back instead of data
    return isinstance(data, dict) and ("error" in data or set(data) == {"message"})


def delete_cache(collection: str, cache_key: str):
    db[collection].delete_one({"key": cache_key})

def _plain(value):
    # numpy scalars (e.g. an id pulled out of a DataFrame) are not JSON serialisable
    if hasattr(value, "item"):
        return value.item()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def get_cache_key(args: dict) -> str:
    key = json.dumps(args, default=_plain)
    return hashlib.md5(key.encode()).hexdigest()


def cache_request(collection: str, expires_hr: int = 72, force: bool = False):
    def decorator(func):
        def wrapped(*args, **kwargs):
            cache_key = get_cache_key(
                {"args": locals()["args"], "kwargs": locals()["kwargs"]}
            )
            if force:
                delete_cache(collection, cache_key)
            try:
                data = get_cache(collection, cache_key)
                if data is None or is_error_response(data):
                    data = func(*args, **kwargs)
                    # an error (e.g. stats not published yet) must not be remembered
                    if not is_error_response(data):
                        set_cache(collection, cache_key, data, expires_hr)
                return data
            except Exception as e:
                print(f"Error in cache_request: {e}")
                return func(*args, **kwargs)

        return wrapped

    return decorator
