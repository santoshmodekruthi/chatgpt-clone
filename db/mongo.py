from pymongo import MongoClient
from config.settings import Settings

settings = Settings()

_client = MongoClient(settings.MONGO_DB_URL, tz_aware=True)
_db = _client[settings.MONGO_DB_NAME]

def get_collection(name: str):
    return _db[name]
