import sys
from db.conversations import create_new_conversation, add_message, get_conversation, get_all_conversations

print("[TEST] Testing MongoDB...", file=sys.stderr)

try:
    print("[TEST] Creating new conversation...", file=sys.stderr)
    conv_id = create_new_conversation(title="Test Conversation", role="user", content="Hello!")
    print(f"[TEST] Created conversation ID: {conv_id}", file=sys.stderr)

    print("[TEST] Adding assistant message...", file=sys.stderr)
    add_message(conv_id, "assistant", "Hi there!")

    print("[TEST] Retrieving conversation...", file=sys.stderr)
    conv = get_conversation(conv_id)
    print(f"[TEST] Retrieved conversation: {conv}", file=sys.stderr)

    print("[TEST] Getting all conversations...", file=sys.stderr)
    all_convs = get_all_conversations()
    print(f"[TEST] All conversations: {all_convs}", file=sys.stderr)

except Exception as e:
    print(f"[TEST] MongoDB Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
