from django.conf import settings
from .ai_exceptions import ChatError

if getattr(settings, "AI_BACKEND", "gemini") == "ollama":
    from .ollama_backend import parse_chat_request
else:
    from .gemini_backend import parse_chat_request