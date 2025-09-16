# website_sales_agent/urls.py (or AI_Sales_Agent/urls.py depending on your folder name)
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("agent/", include("agent.urls")), 
]
