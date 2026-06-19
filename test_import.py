import sys
print("[DEBUG] Python path:", sys.path)

print("\n[DEBUG] Testing import from services.get_title...")
try:
    from services.get_title import get_chat_title
    print("[DEBUG] SUCCESS: Imported get_chat_title!")
    print(f"[DEBUG] Function: {get_chat_title}")
except Exception as e:
    print(f"[DEBUG] ERROR importing: {e}")
    import traceback
    traceback.print_exc()
