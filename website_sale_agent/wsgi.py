# wsgi.py placeholder
"""
WSGI config for website_sale_agent project.

It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'website_sale_agent.settings')

application = get_wsgi_application()
