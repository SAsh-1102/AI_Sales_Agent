from django.db import models


class ChatMessage(models.Model):
    session_id = models.CharField(max_length=100)  # ek chat session ka ID
    sender = models.CharField(max_length=10, choices=[("user", "User"), ("agent", "Agent")])
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)  # auto save time

    def __str__(self):
        return f"[{self.session_id}] {self.sender}: {self.message[:30]}"


