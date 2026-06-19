import sys
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pymongo import DESCENDING

# Try to import and use MongoDB, fall back to in-memory storage if it fails
_use_mongo = True
_in_memory_conversations = {}
conversations = None

try:
    from db.mongo import get_collection
    conversations = get_collection("conversations")
    if conversations:
        print("Creating index on conversations.last_interacted...", file=sys.stderr)
        conversations.create_index([("last_interacted", DESCENDING)])
        print("✅ Using MongoDB for storage!", file=sys.stderr)
        _use_mongo = True
    else:
        print("⚠️ get_collection() returned None, falling back to in-memory storage!", file=sys.stderr)
        _use_mongo = False
except Exception as e:
    print(f"❌ Could not connect to MongoDB: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    print("⚠️ Falling back to in-memory storage (data will be lost when app restarts)!", file=sys.stderr)
    _use_mongo = False


# ----- Helper Functions -----
def now_utc() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def create_new_conversation_id() -> str:
    """Generate a new unique conversation ID"""
    return str(uuid.uuid4())


# ----- Core Conversation Services -----
def create_new_conversation(title: Optional[str] = None, role: Optional[str] = None, content: Optional[str] = None) -> str:
    """Create a new conversation with optional initial message"""
    conv_id = create_new_conversation_id()
    ts = now_utc()
    doc = {
        "_id": conv_id,
        "title": title or "Untitled Conversation",
        "messages": [],
        "last_interacted": ts,
    }
    if role and content:
        doc["messages"].append({
            "role": role,
            "content": content,
            "ts": ts,
            "liked": None  # None = not rated, True = liked, False = disliked
        })
    
    print(f"📝 Creating new conversation with ID: {conv_id}, title: {doc['title']}", file=sys.stderr)
    
    if _use_mongo and conversations:
        try:
            print(f"  Inserting into MongoDB...", file=sys.stderr)
            result = conversations.insert_one(doc)
            print(f"  ✅ Successfully inserted into MongoDB, inserted_id: {result.inserted_id}", file=sys.stderr)
        except Exception as e:
            print(f"  ❌ Error inserting into MongoDB: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
    else:
        _in_memory_conversations[conv_id] = doc
        print(f"  ✅ Successfully inserted into in-memory storage", file=sys.stderr)
    
    return conv_id


def add_message(conv_id: str, role: str, content: str) -> bool:
    """Add a new message to an existing conversation"""
    ts = now_utc()
    print(f"📝 Adding message to conversation {conv_id}: role={role}, content length={len(content)}", file=sys.stderr)
    
    if _use_mongo and conversations:
        try:
            res = conversations.update_one(
                {"_id": conv_id},
                {
                    "$push": {"messages": {
                        "role": role,
                        "content": content,
                        "ts": ts,
                        "liked": None
                    }},
                    "$set": {"last_interacted": ts},
                },
            )
            print(f"  ✅ MongoDB update_one: matched_count={res.matched_count}, modified_count={res.modified_count}", file=sys.stderr)
            return res.matched_count == 1
        except Exception as e:
            print(f"  ❌ Error adding message to MongoDB: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False
    else:
        if conv_id in _in_memory_conversations:
            _in_memory_conversations[conv_id]["messages"].append({
                "role": role,
                "content": content,
                "ts": ts,
                "liked": None
            })
            _in_memory_conversations[conv_id]["last_interacted"] = ts
            print(f"  ✅ Successfully added message to in-memory storage", file=sys.stderr)
            return True
        else:
            print(f"  ❌ Conversation {conv_id} not found in in-memory storage", file=sys.stderr)
            return False


def get_conversation(conv_id: str) -> Optional[Dict[str, Any]]:
    """Get a conversation by ID and update last interacted time"""
    ts = now_utc()
    print(f"📝 Getting conversation: {conv_id}", file=sys.stderr)
    
    if _use_mongo and conversations:
        try:
            doc = conversations.find_one_and_update(
                {"_id": conv_id},
                {"$set": {"last_interacted": ts}},
                return_document=True,
            )
            if doc:
                print(f"  ✅ Found conversation in MongoDB: {doc['title']}, {len(doc['messages'])} messages", file=sys.stderr)
            else:
                print(f"  ⚠️ Conversation {conv_id} not found in MongoDB", file=sys.stderr)
            return doc
        except Exception as e:
            print(f"  ❌ Error getting conversation from MongoDB: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return None
    else:
        if conv_id in _in_memory_conversations:
            _in_memory_conversations[conv_id]["last_interacted"] = ts
            print(f"  ✅ Found conversation in in-memory storage: {_in_memory_conversations[conv_id]['title']}", file=sys.stderr)
            return _in_memory_conversations[conv_id]
        else:
            print(f"  ⚠️ Conversation {conv_id} not found in in-memory storage", file=sys.stderr)
            return None


def get_all_conversations(search_query: Optional[str] = None) -> Dict[str, str]:
    """Get all conversations, optionally filtered by search query"""
    print(f"📝 Getting all conversations (search: {search_query})", file=sys.stderr)
    
    if _use_mongo and conversations:
        try:
            query = {}
            if search_query:
                query = {"$or": [
                    {"title": {"$regex": search_query, "$options": "i"}},
                    {"messages.content": {"$regex": search_query, "$options": "i"}}
                ]}
            cursor = conversations.find(query, {"title": 1}).sort("last_interacted", DESCENDING)
            results = {doc["_id"]: doc["title"] for doc in cursor}
            print(f"  ✅ Found {len(results)} conversations in MongoDB", file=sys.stderr)
            return results
        except Exception as e:
            print(f"  ❌ Error getting all conversations from MongoDB: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return {}
    else:
        # Filter in-memory conversations
        filtered = {}
        for conv_id, conv in _in_memory_conversations.items():
            if not search_query:
                filtered[conv_id] = conv["title"]
            else:
                query_lower = search_query.lower()
                if (query_lower in conv["title"].lower() or
                        any(query_lower in msg["content"].lower() for msg in conv["messages"])):
                    filtered[conv_id] = conv["title"]
        # Sort by last_interacted descending
        sorted_conv = sorted(filtered.items(), key=lambda x: _in_memory_conversations[x[0]]["last_interacted"], reverse=True)
        results = dict(sorted_conv)
        print(f"  ✅ Found {len(results)} conversations in in-memory storage", file=sys.stderr)
        return results


# ----- New Feature Functions -----
def rename_conversation(conv_id: str, new_title: str) -> bool:
    """Rename an existing conversation"""
    print(f"📝 Renaming conversation {conv_id} to: {new_title}", file=sys.stderr)
    
    if _use_mongo and conversations:
        try:
            res = conversations.update_one(
                {"_id": conv_id},
                {"$set": {"title": new_title, "last_interacted": now_utc()}}
            )
            print(f"  ✅ MongoDB update_one for rename: matched_count={res.matched_count}", file=sys.stderr)
            return res.matched_count == 1
        except Exception as e:
            print(f"  ❌ Error renaming conversation in MongoDB: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False
    else:
        if conv_id in _in_memory_conversations:
            _in_memory_conversations[conv_id]["title"] = new_title
            _in_memory_conversations[conv_id]["last_interacted"] = now_utc()
            print(f"  ✅ Successfully renamed conversation in in-memory storage", file=sys.stderr)
            return True
        return False


def delete_conversation(conv_id: str) -> bool:
    """Delete a conversation by ID"""
    print(f"📝 Deleting conversation: {conv_id}", file=sys.stderr)
    
    if _use_mongo and conversations:
        try:
            res = conversations.delete_one({"_id": conv_id})
            print(f"  ✅ MongoDB delete_one: deleted_count={res.deleted_count}", file=sys.stderr)
            return res.deleted_count == 1
        except Exception as e:
            print(f"  ❌ Error deleting conversation from MongoDB: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False
    else:
        if conv_id in _in_memory_conversations:
            del _in_memory_conversations[conv_id]
            print(f"  ✅ Successfully deleted conversation from in-memory storage", file=sys.stderr)
            return True
        return False


def update_message_like(conv_id: str, message_index: int, liked: Optional[bool]) -> bool:
    """Update like/dislike status of a specific message"""
    print(f"📝 Updating like status for conversation {conv_id}, message index {message_index}, liked={liked}", file=sys.stderr)
    
    if _use_mongo and conversations:
        try:
            update_key = f"messages.{message_index}.liked"
            res = conversations.update_one(
                {"_id": conv_id},
                {"$set": {update_key: liked, "last_interacted": now_utc()}}
            )
            print(f"  ✅ MongoDB update_one for like: matched_count={res.matched_count}", file=sys.stderr)
            return res.matched_count == 1
        except Exception as e:
            print(f"  ❌ Error updating like status in MongoDB: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False
    else:
        if conv_id in _in_memory_conversations and 0 <= message_index < len(_in_memory_conversations[conv_id]["messages"]):
            _in_memory_conversations[conv_id]["messages"][message_index]["liked"] = liked
            _in_memory_conversations[conv_id]["last_interacted"] = now_utc()
            print(f"  ✅ Successfully updated like status in in-memory storage", file=sys.stderr)
            return True
        return False


def update_message_content(conv_id: str, message_index: int, new_content: str) -> bool:
    """Update content of a specific message (for regenerate feature)"""
    print(f"📝 Updating message content for conversation {conv_id}, message index {message_index}", file=sys.stderr)
    
    if _use_mongo and conversations:
        try:
            update_key = f"messages.{message_index}.content"
            res = conversations.update_one(
                {"_id": conv_id},
                {"$set": {update_key: new_content, "last_interacted": now_utc()}}
            )
            print(f"  ✅ MongoDB update_one for content: matched_count={res.matched_count}", file=sys.stderr)
            return res.matched_count == 1
        except Exception as e:
            print(f"  ❌ Error updating message content in MongoDB: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            return False
    else:
        if conv_id in _in_memory_conversations and 0 <= message_index < len(_in_memory_conversations[conv_id]["messages"]):
            _in_memory_conversations[conv_id]["messages"][message_index]["content"] = new_content
            _in_memory_conversations[conv_id]["last_interacted"] = now_utc()
            print(f"  ✅ Successfully updated message content in in-memory storage", file=sys.stderr)
            return True
        return False
