import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from shop.models import Category

# find and update the category

category = Category.objects.get(name="Earbuds and Earphones")
category.name = "Earbuds and Headphones"
category.save()

print("Category updated successfully!")