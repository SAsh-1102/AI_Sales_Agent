# urls.py placeholder for agent
from django.urls import path
from . import views

urlpatterns = [
    path("chat/", views.chat_api, name="chat_api"),
    path("voice/", views.voice_api, name="voice_api"),  # NEW voice endpoint
]

