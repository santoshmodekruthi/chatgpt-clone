import sys
from groq import Groq
from config.settings import Settings

print("[DEBUG] Loading settings...")
settings = Settings()
print(f"[DEBUG] GROQ_API_KEY loaded: {'Yes (first 10 chars): ' + settings.GROQ_API_KEY[:10] + '...' if len(settings.GROQ_API_KEY) > 10 else 'Yes'}")

print("\n[DEBUG] Creating Groq client...")
client = Groq(api_key=settings.GROQ_API_KEY)

print("\n[DEBUG] Testing Groq chat completion...")
try:
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "user", "content": "Hello! What's your name?"}
        ],
        model="llama-3.3-70b-versatile"
    )
    print(f"[DEBUG] Groq response: {chat_completion.choices[0].message.content}")
    print("\n✅ Groq integration is working perfectly!")
except Exception as e:
    print(f"[DEBUG] ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\n❌ Please check your GROQ_API_KEY in the .env file.")
