import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")
django.setup()

from shop.models import Category, Product, ProductVariant, ProductSize


def find_category_ids(targets):
    ids = set()
    for t in targets:
        if isinstance(t, int):
            ids.add(t)
        elif isinstance(t, str):
            for c in Category.objects.filter(name=t):
                ids.add(c.id)
    return list(ids)


def rename_categories(mapping):
    for ident, new_name in mapping.items():
        cats = Category.objects.filter(id=ident) if isinstance(ident, int) else Category.objects.filter(name=ident)
        for c in cats:
            old = c.name
            c.name = new_name
            c.save()
            print(f"Renamed category {c.id} from '{old}' to '{c.name}'")


def delete_products_in_categories(category_ids):
    if not category_ids:
        print("No category IDs provided for deletion")
        return
    products = Product.objects.filter(category_id__in=category_ids)
    product_ids = list(products.values_list("id", flat=True))
    print(f"Deleting {len(product_ids)} products in categories {category_ids}")
    if product_ids:
        ProductSize.objects.filter(variant__product_id__in=product_ids).delete()
        ProductVariant.objects.filter(product_id__in=product_ids).delete()
        products.delete()
    print("Deletion complete")


if __name__ == "__main__":
    # Desired renames
    rename_map = {
        36: "Drones",  # parent category if applicable
        37: "Drones",
        38: "Drone Parts",
        "Phone Cases": "Drones",
        "Tripods": "Drone Parts",
    }
    rename_categories(rename_map)

    target_ids = find_category_ids([37, 38, "Phone Cases", "Tripods"])
    delete_products_in_categories(target_ids)
    print("Done.")


