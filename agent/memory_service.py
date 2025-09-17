# agent/memory_service.py
from .models import ChatMessage  # Import your Django model
from datetime import datetime
import pytz

PAKISTAN_TZ = pytz.timezone("Asia/Karachi")

def save_message(session_id, sender, message):
    timestamp = datetime.now(PAKISTAN_TZ)
    # DB me save karein
    message_obj = ChatMessage.objects.create(
        session_id=session_id,
        sender=sender,
        message=message,
        timestamp=timestamp
    )
    return message_obj

def get_history(session_id, limit=10):
    return ChatMessage.objects.filter(session_id=session_id).order_by("-timestamp")[:limit][::-1]
