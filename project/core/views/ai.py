import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..ai import parse_chat_request, ChatError

@require_POST
def chat(request):
    # Get chat_type, message, and history
    chat_type = request.POST.get("chat_type", "")
    message = request.POST.get("message", "").strip()

    # Try to get history
    try:
        history = json.loads(request.POST.get("history", "[]"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Chat history must be valid JSON."}, status=400)

    # Try to get reply
    try:
        reply = parse_chat_request(chat_type, message, history)
    except ChatError as e:
        # Error. Return the error message and status code
        return JsonResponse({"error": str(e)}, status=e.status)

    # No error, return reply
    return JsonResponse({"reply": reply.strip()})