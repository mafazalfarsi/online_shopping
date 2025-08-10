from django.contrib import admin
from .models import Category, Product, ProductVariant, ProductSize, Order, OrderItem, User


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'category', 'brand', 'availability']
    list_filter = ['category', 'brand', 'availability']
    search_fields = ['name', 'description', 'brand']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'price', 'category', 'image_url')
        }),
        ('Product Details', {
            'fields': ('about_product', 'key_features', 'specifications')
        }),
        ('Product Information', {
            'fields': ('brand', 'warranty', 'availability')
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'custom_emoji']
    list_filter = ['parent']
    search_fields = ['name']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'parent')
        }),
        ('Display', {
            'fields': ('custom_emoji',)
        }),
    )
admin.site.register(ProductVariant)
admin.site.register(ProductSize)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer_name', 'order_date', 'total_amount', 'status']
    list_filter = ['status', 'order_date']
    search_fields = ['order_id', 'customer_name', 'customer_phone']
    inlines = [OrderItemInline]
    readonly_fields = ['order_date']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'created_at']
    list_filter = ['created_at']
    search_fields = ['username', 'email']
    readonly_fields = ['created_at']





