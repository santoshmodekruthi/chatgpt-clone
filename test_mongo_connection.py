import sys
from pymongo import MongoClient
from config.settings import Settings

print("=== MongoDB Connection Test ===")

try:
    settings = Settings()
    print("Loaded settings...")
    print(f"MONGO_DB_URL (first 50 chars): {settings.MONGO_DB_URL[:50]}...")
    print(f"MONGO_DB_NAME: {settings.MONGO_DB_NAME}")
    print("\nConnecting to MongoDB...")
    
    client = MongoClient(
        settings.MONGO_DB_URL,
        tz_aware=True,
        tls=True,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    print("Client created! Testing connection...")
    
    # Test the connection
    client.admin.command('ping')
    print("Ping successful! Connected to MongoDB!")
    
    # Check the database
    db = client[settings.MONGO_DB_NAME]
    print(f"Database '{settings.MONGO_DB_NAME}' exists!")
    
    # Check collections
    collections = db.list_collection_names()
    print(f"Collections: {collections}")
    
    # Test inserting a test document
    test_coll = db['test_collection']
    test_doc = {"test": "hello", "ts": "now"}
    result = test_coll.insert_one(test_doc)
    print(f"Test document inserted with ID: {result.inserted_id}")
    
    # Clean up test document
    test_coll.delete_one({"_id": result.inserted_id})
    print("Test document deleted!")
    
    print("\n=== All MongoDB tests passed! ===")
    
except Exception as e:
    print(f"\nMongoDB ERROR: {str(e)}")
    print("\nStack Trace:")
    import traceback
    traceback.print_exc()
    sys.exit(1)
