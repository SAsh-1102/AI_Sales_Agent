from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),  # root of /agent/
    path("chat/", views.chat_api, name="chat_api"),
    path("voice/", views.voice_api, name="voice_api"),
]
