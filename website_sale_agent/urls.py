# urls.py placeholder
from django.contrib import admin
from django.urls import path
from agent import views

urlpatterns = [
    path("", views.home, name="home"),
    path("agent/chat/", views.chat_api, name="chat_api"),
    path("agent/voice/", views.voice_api, name="voice_api"),  # ✅ add this
    path("admin/", admin.site.urls),
]




