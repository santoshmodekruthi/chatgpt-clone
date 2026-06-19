from config.settings import Settings

settings = Settings()


def get_ollama_models_list():
    # Return list of popular Groq models
    return [
        "llama-3.3-70b-versatile",
        "llama-3.1-70b-versatile",
        "llama-3.1-8b-instant",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]
