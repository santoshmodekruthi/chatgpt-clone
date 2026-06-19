import sys
from services.get_models_list import get_ollama_models_list
from services.get_title import get_chat_title
from services.chat_utilities import get_answer
from db.conversations import create_new_conversation, add_message, get_conversation, get_all_conversations

print("[TEST FULL FLOW] Starting...", file=sys.stderr)

# Step 1: Get models
print("\n[TEST] Step 1: Getting models list...", file=sys.stderr)
try:
    models = get_ollama_models_list()
    print(f"[TEST] Models: {models}", file=sys.stderr)
    selected_model = models[1]  # llama3:latest
    print(f"[TEST] Selected model: {selected_model}", file=sys.stderr)
except Exception as e:
    print(f"[TEST ERROR] Step 1: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Step 2: Simulate user message
user_query = "Hello"
print(f"\n[TEST] Step 2: User query: {user_query}", file=sys.stderr)

# Step 3: Create conversation (with default title first)
print("\n[TEST] Step 3: Creating conversation...", file=sys.stderr)
try:
    title = "New Chat"
    conv_id = create_new_conversation(title=title, role="user", content=user_query)
    print(f"[TEST] Conversation created with ID: {conv_id}", file=sys.stderr)
except Exception as e:
    print(f"[TEST ERROR] Step 3: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Step 4: Chat history
chat_history = [{"role": "user", "content": user_query}]
print(f"\n[TEST] Step 4: Chat history: {chat_history}", file=sys.stderr)

# Step 5: Get assistant response - THIS IS THE CRITICAL PART!
print("\n[TEST] Step 5: Calling get_answer()...", file=sys.stderr)
try:
    print("[TEST] About to call get_answer...", file=sys.stderr)
    assistant_text = get_answer(selected_model, chat_history)
    print(f"[TEST SUCCESS!] Assistant response: {assistant_text}", file=sys.stderr)
except Exception as e:
    print(f"[TEST ERROR] Step 5: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

# Step 6: Add assistant message
print("\n[TEST] Step 6: Adding assistant message...", file=sys.stderr)
try:
    add_message(conv_id, "assistant", assistant_text)
    print("[TEST] Assistant message added!", file=sys.stderr)
except Exception as e:
    print(f"[TEST ERROR] Step 6: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

print("\n[TEST FULL FLOW] All steps completed SUCCESSFULLY!", file=sys.stderr)
