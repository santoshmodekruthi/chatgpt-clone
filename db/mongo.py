import sys
import certifi
from pymongo import MongoClient
from config.settings import Settings

settings = Settings()

print("=== Initializing MongoDB Client ===", file=sys.stderr)
print(f"MONGO_DB_URL: {settings.MONGO_DB_URL[:50]}...", file=sys.stderr)
print(f"MONGO_DB_NAME: {settings.MONGO_DB_NAME}", file=sys.stderr)

# Configure MongoDB client with certifi for proper SSL
_client = MongoClient(
    settings.MONGO_DB_URL,
    tz_aware=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=30000,
    socketTimeoutMS=30000
)

try:
    # Test the connection
    print("Testing MongoDB connection with ping...", file=sys.stderr)
    _client.admin.command('ping')
    print("✅ MongoDB client connected successfully!", file=sys.stderr)
    
    # List databases to verify access
    print(f"Available databases: {_client.list_database_names()}", file=sys.stderr)
    
    _db = _client[settings.MONGO_DB_NAME]
    print(f"✅ Using database: {settings.MONGO_DB_NAME}", file=sys.stderr)
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    _db = None

def get_collection(name: str):
    if _db:
        coll = _db[name]
        print(f"✅ Using collection: {name}", file=sys.stderr)
        return coll
    else:
        print(f"❌ MongoDB not connected, cannot get collection: {name}", file=sys.stderr)
        return None
