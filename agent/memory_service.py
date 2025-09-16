from agent.models import ChatMessage

def save_message(session_id, sender, message):
    ChatMessage.objects.create(
        session_id=session_id,
        sender=sender,
        message=message
    )

def get_history(session_id, limit=10):
    return ChatMessage.objects.filter(session_id=session_id).order_by("-timestamp")[:limit][::-1]


