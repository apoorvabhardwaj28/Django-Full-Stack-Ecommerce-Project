import os
from django.conf import settings
from django.utils.text import slugify
from products.models import Category, Product

media_products_path = os.path.join(settings.BASE_DIR, "media", "products")

print("Looking inside:", media_products_path)

allowed_extensions = (".jpg", ".jpeg", ".png", ".webp")

category, _ = Category.objects.get_or_create(
    slug="general",
    defaults={"name": "General"}
)

created = 0
skipped = 0

for filename in os.listdir(media_products_path):

    if not filename.lower().endswith(allowed_extensions):
        continue

    name_without_ext = os.path.splitext(filename)[0]

    product_name = name_without_ext.replace("_", " ").replace("-", " ").title()
    slug = slugify(product_name)

    if Product.objects.filter(slug=slug).exists():
        skipped += 1
        continue

    Product.objects.create(
        category=category,
        name=product_name,
        slug=slug,
        description=f"{product_name} product",
        image=f"products/{filename}",
        price=999,
        stock=10,
        available=True
    )

    created += 1
    print("Created:", product_name)

print(f"Done! {created} products created, {skipped} skipped.")