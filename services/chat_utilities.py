import sys
from groq import Groq
from config.settings import Settings

settings = Settings()
client = Groq(api_key=settings.GROQ_API_KEY.strip())


def get_answer(model_name, chat_history):
    """Get a complete answer from Groq (non-streaming)"""
    print(f"[DEBUG] get_answer called with model: {model_name}", file=sys.stderr)
    
    messages = [
        {"role": "system", "content": "You are a helpful, friendly, and knowledgeable AI assistant. Always provide clear, detailed, and well-structured answers. Use markdown formatting when appropriate (like headings, bullet points, code blocks, etc.)."}
    ]
    messages.extend(chat_history)
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[DEBUG] get_answer error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise


def get_streaming_answer(model_name, chat_history):
    """Get a streaming answer from Groq (returns a generator)"""
    print(f"[DEBUG] get_streaming_answer called with model: {model_name}", file=sys.stderr)
    
    messages = [
        {"role": "system", "content": "You are a helpful, friendly, and knowledgeable AI assistant. Always provide clear, detailed, and well-structured answers. Use markdown formatting when appropriate (like headings, bullet points, code blocks, etc.)."}
    ]
    messages.extend(chat_history)
    
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            stream=True
        )
        
        for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"[DEBUG] get_streaming_answer error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise
