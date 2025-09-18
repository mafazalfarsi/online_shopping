import os
import django

# Configure Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from shop.models import Category, Product


def delete_products_in_subcategories(subcategory_identifiers):
    """
    Delete products that belong to any of the provided subcategories.

    subcategory_identifiers can contain category IDs (ints/str) or names (str).
    """
    ids = set()
    names = set()

    for ident in subcategory_identifiers:
        try:
            ids.add(int(ident))
        except (TypeError, ValueError):
            if isinstance(ident, str):
                names.add(ident.strip())

    categories = Category.objects.none()

    if ids:
        categories = categories.union(Category.objects.filter(id__in=list(ids)))
    if names:
        categories = categories.union(Category.objects.filter(name__in=list(names)))

    if not categories.exists():
        print("No matching subcategories found.")
        return

    category_ids = list(categories.values_list("id", flat=True))
    print(f"Target subcategory IDs: {category_ids}")

    qs = Product.objects.filter(category_id__in=category_ids)
    count = qs.count()
    qs.delete()
    print(f"Deleted {count} products from subcategories {category_ids}.")


if __name__ == "__main__":
    # Default targets: Phone Cases (37), Tripods (38) by both ID and name
    default_targets = [37, 38, "Phone Cases", "Tripods"]
    delete_products_in_subcategories(default_targets)


