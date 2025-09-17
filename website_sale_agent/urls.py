from django.contrib import admin
from django.urls import path, include
from agent.views import index  # for homepage

urlpatterns = [
    path("admin/", admin.site.urls),    # Admin panel
    path("agent/", include("agent.urls")),  # Agent API
    path("", index, name="home"),       # Homepage at '/'
]
