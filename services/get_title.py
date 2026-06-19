import sys
from groq import Groq
from config.settings import Settings

settings = Settings()
client = Groq(api_key=settings.GROQ_API_KEY)


def get_chat_title(model, user_query):
    print(f"[DEBUG] get_chat_title called with model: {model}, query: {user_query}", file=sys.stderr)
    
    system_prompt = """You are a helpful assistant that generates short, clear, and catchy titles.
    Task:
    - Read the given user query.
    - Create a concise title (max 7 words).
    - The title should summarize the intent of the query.
    - Avoid unnecessary words, punctuation, or filler.
    - Keep it professional and easy to understand.
    - Only output the title, no extra text!"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ],
            temperature=0.3,
            max_tokens=30
        )
        title = response.choices[0].message.content.strip()
        print(f"[DEBUG] Generated title: {title}", file=sys.stderr)
        return title
    except Exception as e:
        print(f"[DEBUG] Title generation error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return "New Chat"
