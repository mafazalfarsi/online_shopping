#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from shop.models import Category

# Define custom emojis for each subcategory
emoji_mapping = {
    # Phone Chargers subcategories
    'Charging Cables': '🔌',
    'Wireless Chargers': '🔋',
    'Cable Accessories': '⚡',
    'Portable Chargers': '🔋',
    
    # Earphones and Headphones subcategories
    'Earbuds': '🎧',
    'Wired Earphones': '🎧',
    'Headphones': '🎧',
    'Earbuds Cases': '🎧',
    
    # PC Accessories subcategories
    'Keyboards': '⌨️',
    'Mouses': '🖱️',
    'Speakers': '🔊',
    
    # Phone Accessories subcategories
    'Phone Cases': '📱',
    'Tripods': '📱',
    
    # Phone Cases subcategories
    'iPhone': '📱',
    'Samsung': '📱',
}

print("=== SETTING CUSTOM EMOJIS FOR SUBCATEGORIES ===")
print()

# Get all subcategories
subcategories = Category.objects.filter(parent__isnull=False)

for subcategory in subcategories:
    if subcategory.name in emoji_mapping:
        old_emoji = subcategory.custom_emoji if subcategory.custom_emoji else "📦"
        new_emoji = emoji_mapping[subcategory.name]
        
        subcategory.custom_emoji = new_emoji
        subcategory.save()
        
        print(f"✅ {old_emoji} {subcategory.name} → {new_emoji} {subcategory.name}")
    else:
        print(f"⚠️  No emoji mapping found for: {subcategory.name}")

print()
print("=== UPDATED SUBCATEGORIES ===")
print()

# Show the updated subcategories
parent_categories = Category.objects.filter(subcategories__isnull=False).distinct()

for parent in parent_categories:
    print(f"📁 {parent.name}")
    subcategories = parent.subcategories.all()
    for sub in subcategories:
        emoji = sub.custom_emoji if sub.custom_emoji else "📦"
        print(f"  └── {emoji} {sub.name}")
    print()

print("🎉 All subcategory emojis have been updated!") 