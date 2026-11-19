from .ai_exceptions import ChatError

def verify_chat_parameters(chat_type, message, history, system_prompts, max_chat_message_length, max_history_messages):
    if chat_type not in system_prompts:
        raise ChatError("Unknown chat type.", status=400)
    if not message:
        raise ChatError("Enter a message before sending.", status=400)
    if len(message) > max_chat_message_length:
        raise ChatError(f"Message must be at most {max_chat_message_length} characters.", status=400)
    
    if not isinstance(history, list) or len(history) > max_history_messages:
        raise ChatError(f"Chat history can contain at most {max_history_messages} messages.", status=400)
    
    for item in history:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("role"), str)
            or item["role"] not in {"user", "assistant"}
            or not isinstance(item.get("content"), str)
            or not item["content"].strip()
            or len(item["content"]) > max_chat_message_length
        ):
            raise ChatError("Chat history contains an invalid message.", status=400)