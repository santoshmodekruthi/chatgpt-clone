import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from pymongo import DESCENDING
from db.mongo import get_collection

# Get conversations collection
conversations = get_collection("conversations")
# Create index for faster sorting
conversations.create_index([("last_interacted", DESCENDING)])


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
    conversations.insert_one(doc)
    return conv_id


def add_message(conv_id: str, role: str, content: str) -> bool:
    """Add a new message to an existing conversation"""
    ts = now_utc()
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
    return res.matched_count == 1


def get_conversation(conv_id: str) -> Optional[Dict[str, Any]]:
    """Get a conversation by ID and update last interacted time"""
    ts = now_utc()
    doc = conversations.find_one_and_update(
        {"_id": conv_id},
        {"$set": {"last_interacted": ts}},
        return_document=True,
    )
    return doc


def get_all_conversations(search_query: Optional[str] = None) -> Dict[str, str]:
    """Get all conversations, optionally filtered by search query"""
    query = {}
    if search_query:
        query = {"$or": [
            {"title": {"$regex": search_query, "$options": "i"}},
            {"messages.content": {"$regex": search_query, "$options": "i"}}
        ]}
    cursor = conversations.find(query, {"title": 1}).sort("last_interacted", DESCENDING)
    return {doc["_id"]: doc["title"] for doc in cursor}


# ----- New Feature Functions -----
def rename_conversation(conv_id: str, new_title: str) -> bool:
    """Rename an existing conversation"""
    res = conversations.update_one(
        {"_id": conv_id},
        {"$set": {"title": new_title, "last_interacted": now_utc()}}
    )
    return res.matched_count == 1


def delete_conversation(conv_id: str) -> bool:
    """Delete a conversation by ID"""
    res = conversations.delete_one({"_id": conv_id})
    return res.deleted_count == 1


def update_message_like(conv_id: str, message_index: int, liked: Optional[bool]) -> bool:
    """Update like/dislike status of a specific message"""
    update_key = f"messages.{message_index}.liked"
    res = conversations.update_one(
        {"_id": conv_id},
        {"$set": {update_key: liked, "last_interacted": now_utc()}}
    )
    return res.matched_count == 1


def update_message_content(conv_id: str, message_index: int, new_content: str) -> bool:
    """Update content of a specific message (for regenerate feature)"""
    update_key = f"messages.{message_index}.content"
    res = conversations.update_one(
        {"_id": conv_id},
        {"$set": {update_key: new_content, "last_interacted": now_utc()}}
    )
    return res.matched_count == 1
