from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    custom_emoji = models.CharField(max_length=10, blank=True, help_text="Custom emoji for this category (e.g., 📱, 🎧, ⌨️)")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"


class Order(models.Model):
    order_id = models.CharField(max_length=10, unique=True)
    customer_name = models.CharField(max_length=100)
    customer_email = models.CharField(max_length=100, blank=True)
    customer_phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='Credit/Debit Card')
    status = models.CharField(max_length=20, default='Pending')
    
    def __str__(self):
        return f"Order #{self.order_id} - {self.customer_name}"
    
    class Meta:
        verbose_name_plural = "Orders"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=200)
    product_id = models.IntegerField(help_text="Product ID from the Product model", null=True, blank=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.product_name} x{self.quantity}"
    
    class Meta:
        verbose_name_plural = "Order Items"  


class Product(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    image_url = models.URLField(max_length=1024, null=True, blank=True)
    
    # New fields for specific product information
    key_features = models.TextField(blank=True, help_text="Enter key features separated by new lines")
    specifications = models.TextField(blank=True, help_text="Enter specifications in format: Label: Value (one per line)")
    about_product = models.TextField(blank=True, help_text="Detailed description about the product")
    brand = models.CharField(max_length=100, blank=True, default="TechMart")
    warranty = models.CharField(max_length=100, blank=True, default="1 Year")
    availability = models.CharField(max_length=100, blank=True, default="In Stock")

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color_name = models.CharField(max_length=50)  # e.g., "Royal Blue"
    color_hex_code = models.CharField(max_length=7, help_text="e.g., #0000FF") # e.g., #0000FF
    image_url = models.URLField(max_length=1024, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    def __str__(self):
        return f"{self.product.name} ({self.color_name})"  


class ProductSize(models.Model):
    variant = models.ForeignKey(ProductVariant, related_name='sizes', on_delete=models.CASCADE)
    size = models.CharField(max_length=5)  # e.g., "S", "M", "L", "XL", or "42", "44", etc.
    stock = models.PositiveIntegerField(default=0)  # inventory per size-color

    def __str__(self):
        return f"{self.variant} - Size {self.size}"


class User(models.Model):
    username = models.CharField(max_length=100, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)  # In a real app, this should be hashed
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.username
    
    class Meta:
        verbose_name_plural = "Users"