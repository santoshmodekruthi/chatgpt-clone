import sys
import os

print("Current directory:", os.getcwd())
print("Python path:", sys.path)

print("\n--- Trying to import services.chat_utilities ---")
try:
    from services import chat_utilities
    print("OK: chat_utilities imported!")
    print(f"Available functions: {dir(chat_utilities)}")
    
    print("\n--- Checking get_streaming_answer ---")
    if hasattr(chat_utilities, 'get_streaming_answer'):
        print("OK: get_streaming_answer exists!")
    else:
        print("ERROR: get_streaming_answer missing!")
        
except Exception as e:
    print(f"ERROR: Import failed: {e}")
    import traceback
    traceback.print_exc()
