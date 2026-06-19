import sys
import requests
from config.settings import Settings
from llama_index.llms.ollama import Ollama

print("[TEST] Loading settings...", file=sys.stderr)
settings = Settings()
print(f"[TEST] MONGO_DB_URL: {settings.MONGO_DB_URL}", file=sys.stderr)
print(f"[TEST] MONGO_DB_NAME: {settings.MONGO_DB_NAME}", file=sys.stderr)
print(f"[TEST] OLLAMA_URL: {settings.OLLAMA_URL}", file=sys.stderr)
print(f"[TEST] OLLAMA_MODELS: {settings.OLLAMA_MODELS}", file=sys.stderr)

print("\n[TEST] Checking Ollama API tags...", file=sys.stderr)
try:
    response = requests.get(f"{settings.OLLAMA_URL}/api/tags")
    print(f"[TEST] Ollama tags response status: {response.status_code}", file=sys.stderr)
    print(f"[TEST] Ollama tags response content: {response.text}", file=sys.stderr)
except Exception as e:
    print(f"[TEST] Error checking Ollama tags: {e}", file=sys.stderr)

print("\n[TEST] Trying to create Ollama LLM instance...", file=sys.stderr)
try:
    llm = Ollama(base_url=settings.OLLAMA_URL, model="llama3:latest")
    print(f"[TEST] LLM instance created: {llm}", file=sys.stderr)
    print("\n[TEST] Trying to send a test message...", file=sys.stderr)
    from llama_index.core.llms import ChatMessage, MessageRole
    messages = [
        ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
        ChatMessage(role=MessageRole.USER, content="Hello, how are you?")
    ]
    response = llm.chat(messages=messages)
    print(f"[TEST] LLM response: {response}", file=sys.stderr)
    print(f"[TEST] Response message content: {response.message.content}", file=sys.stderr)
except Exception as e:
    print(f"[TEST] Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
