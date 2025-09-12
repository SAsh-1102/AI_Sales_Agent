from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("agent.urls")),  # 👈 ye line zaroori hai
]









