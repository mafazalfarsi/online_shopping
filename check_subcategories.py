#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from shop.models import Category

print("=== EXISTING SUBCATEGORIES ===")
print()

# Get all categories that have subcategories
parent_categories = Category.objects.filter(subcategories__isnull=False).distinct()

for parent in parent_categories:
    print(f"📁 {parent.name} (ID: {parent.id})")
    subcategories = parent.subcategories.all()
    for sub in subcategories:
        current_emoji = sub.custom_emoji if sub.custom_emoji else "📦"
        print(f"  └── {current_emoji} {sub.name} (ID: {sub.id})")
    print()

print("=== TOTAL SUBCATEGORIES ===")
subcategories = Category.objects.filter(parent__isnull=False)
print(f"Found {subcategories.count()} subcategories:")
for sub in subcategories:
    current_emoji = sub.custom_emoji if sub.custom_emoji else "📦"
    print(f"  {current_emoji} {sub.name} (ID: {sub.id}) - Parent: {sub.parent.name}") 