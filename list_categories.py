import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from shop.models import Category, Product

print("ID | Name | Parent | ProductCount")
for c in Category.objects.order_by('id'):
    print(f"{c.id} | {c.name} | {c.parent_id} | {Product.objects.filter(category=c).count()}")


