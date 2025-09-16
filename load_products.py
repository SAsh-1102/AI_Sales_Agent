import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "website_sale_agent.settings")
django.setup()

from agent.models import Product
from agent.products_data import products   # dataset import

for item in products:
    Product.objects.update_or_create(
        model=item["model"],   # Unique field
        defaults=item
    )

print("Products inserted/updated successfully!")


