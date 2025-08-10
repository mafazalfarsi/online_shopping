from django import forms
from .models import Product, Category, ProductVariant, ProductSize

class AddToCartForm(forms.Form):
    variant_id = forms.IntegerField()
    size = forms.IntegerField()

class AddProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'image_url', 'about_product', 'key_features', 'specifications', 'brand', 'warranty', 'availability']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief product description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Image URL (optional)'}),
            'about_product': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed description about the product...'}),
            'key_features': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Enter key features (one per line):\n• High-quality materials\n• Modern design\n• Durable construction\n• User-friendly interface'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Enter specifications (format: Label: Value):\nBrand: TechMart\nWarranty: 1 Year\nConnectivity: USB-C\nWeight: 1.2kg'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand name'}),
            'warranty': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Warranty information'}),
            'availability': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Stock status'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show all categories for adding products
        categories = Category.objects.all()
        self.fields['category'].queryset = categories
        # Also set choices explicitly
        self.fields['category'].choices = [('', 'Select a category')] + [(cat.id, cat.name) for cat in categories]
            

class EditProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'category', 'image_url', 'about_product', 'key_features', 'specifications', 'brand', 'warranty', 'availability']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Brief product description'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Price', 'step': '0.01'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Image URL (optional)'}),
            'about_product': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed description about the product...'}),
            'key_features': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Enter key features (one per line):\n• High-quality materials\n• Modern design\n• Durable construction\n• User-friendly interface'}),
            'specifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Enter specifications (format: Label: Value):\nBrand: TechMart\nWarranty: 1 Year\nConnectivity: USB-C\nWeight: 1.2kg'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brand name'}),
            'warranty': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Warranty information'}),
            'availability': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Stock status'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show all categories for editing
        categories = Category.objects.all()
        self.fields['category'].queryset = categories
        # Also set choices explicitly
        self.fields['category'].choices = [('', 'Select a category')] + [(cat.id, cat.name) for cat in categories]
            