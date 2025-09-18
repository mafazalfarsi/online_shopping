import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Product, Category, ProductVariant, ProductSize, Order, OrderItem, User, SavedAddress, SavedPaymentMethod
from .forms import AddProductForm, EditProductForm
from .thawani_service import ThawaniPayService
from decimal import Decimal
import random
import string


def test_view(request):
    print(f"=== TEST VIEW CALLED ===")
    return render(request, 'shop/test.html', {'message': 'Test page works!'})

def simple_login_test(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username == 'admin' and password == '123':
            return render(request, 'shop/test.html', {'message': 'Simple login test successful'})
        else:
            return render(request, 'shop/test.html', {'message': 'Login failed'})
    
    return render(request, 'shop/test.html', {'message': 'Simple login test page'})

def minimal_test(request):
    print(f"=== MINIMAL TEST CALLED ===")
    return HttpResponse("Minimal test works!")


def home(request):
    # Show all products on the home page
    products = Product.objects.all()
    # Get all top-level categories for navigation
    categories = Category.objects.filter(parent__isnull=True)
    

    
    # Option 1: Get first 4 products (current)
    # top_picks = Product.objects.all()[:4]
    
    # Option 2: Get most expensive products
    # top_picks = Product.objects.order_by('-price')[:4]
    
    # Option 3: Get newest products (by ID)
    # top_picks = Product.objects.order_by('-id')[:4]
    
    # Option 4: Get products from specific category
    # top_picks = Product.objects.filter(category__name='Electronics')[:4]
    
    # Option 5: Get products with images
    # top_picks = Product.objects.exclude(image_url='')[:4]
    
    # Option 6: Get random products
    # top_picks = Product.objects.order_by('?')[:4]
    
    # Option 7: Get products by name containing specific words
    # top_picks = Product.objects.filter(name__icontains='phone')[:4]
    
    # Option 8: Get specific products by ID (NEW OPTION)
    # Replace the IDs below with the ones you want to show
    top_picks = Product.objects.filter(id__in=[32, 21, 38, 16])  # Apple Airpods 4, Apple airpods 4 ANC, Airpods Max, Apple Magic Keyboard
    
    # Get newest products (by ID - newest first)
    new_arrivals = Product.objects.order_by('-id')[:4]
    
    return render(request, 'shop/home.html', {
        'products': products, 
        'categories': categories,
        'top_picks': top_picks,
        'new_arrivals': new_arrivals
    })


def category_list(request):
    # Only show top-level categories (categories without parents)
    categories = Category.objects.filter(parent__isnull=True)
    return render(request, 'shop/category_list.html', {'categories': categories})

def product_list_by_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    
    # Get all top-level categories for navigation
    categories = Category.objects.filter(parent__isnull=True)
    
    # Get all products in this category and its subcategories
    products = Product.objects.filter(category=category)
    
    # Also get products from subcategories
    subcategories = Category.objects.filter(parent=category)
    for subcategory in subcategories:
        subcategory_products = Product.objects.filter(category=subcategory)
        products = products.union(subcategory_products)
    
    # Show products page with all products from this category and subcategories
    context = {'category': category, 'products': products, 'categories': categories}
    return render(request, 'shop/product_list.html', context)


def cart_detail(request):
    cart = request.session.get('cart', {})
    items = []
    total_price = 0

    for cart_key, quantity in cart.items():
        try:
            # Check if this is a simple product (no variants)
            if '-' not in cart_key:
                product = Product.objects.get(id=int(cart_key))
                item_total = product.price * quantity
                items.append({
                    'product': product,
                    'variant': None,
                    'size': None,
                    'quantity': quantity,
                    'total_price': item_total,
                    'cart_key': cart_key,
                })
                total_price += item_total
            else:
                # Handle products with variants (legacy support)
                variant_id, size_id = cart_key.split('-')
                variant_id = int(variant_id)
                size_id = int(size_id)
                variant = ProductVariant.objects.get(id=variant_id)
                size = ProductSize.objects.get(id=size_id)
                product = variant.product
                item_total = variant.price * quantity
                items.append({
                    'product': product,
                    'variant': variant,
                    'size': size,
                    'quantity': quantity,
                    'total_price': item_total,
                    'cart_key': cart_key,
                })
                total_price += item_total
        except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist):
            continue  # Skip if the product doesn't exist

    # Calculate delivery fee
    from decimal import Decimal
    delivery_fee = Decimal('2.0') if total_price < Decimal('20.0') else Decimal('0.0')
    final_total = total_price + delivery_fee
    
    context = {
        'cart': {
            'items': items,
            'total_price': total_price,
            'delivery_fee': delivery_fee,
            'final_total': final_total,
        }
    }
    return render(request, 'shop/cart_detail.html', context)


def checkout(request):
    # Check if user is logged in
    if not request.session.get('is_logged_in') and not request.session.get('is_admin'):
        # Store the intended destination in session
        request.session['next_url'] = 'checkout'
        return redirect('login')
    
    # Get saved addresses for the user
    username = request.session.get('username')
    saved_addresses = []
    categories = Category.objects.filter(parent__isnull=True)
    
    try:
        user, created = User.objects.get_or_create(username=username)
        saved_addresses = SavedAddress.objects.filter(user=user).order_by('-is_primary', '-created_at')
    except:
        pass
    
    if request.method == 'POST':
        # Here you would normally save the order and user info to the database
        # For now, just store info in session and redirect
        request.session['order_info'] = {
            'name': request.POST.get('name'),
            'address': request.POST.get('address'),
            'city': request.POST.get('city'),
            'postal_code': request.POST.get('postal_code'),
            'phone': request.POST.get('phone'),
            'saved_address_id': request.POST.get('saved_address_id'),  # New field
        }
        
        # If a saved address was chosen, hydrate full address/contact fields into session
        saved_address_id = request.POST.get('saved_address_id')
        if saved_address_id:
            try:
                username = request.session.get('username')
                user, _ = User.objects.get_or_create(username=username)
                sa = SavedAddress.objects.get(id=int(saved_address_id), user=user)
                # Update order_info with saved address details
                order_info = request.session.get('order_info', {})
                order_info.update({
                    'name': sa.name or order_info.get('name'),
                    'address': sa.address or order_info.get('address', ''),
                    'city': sa.city or order_info.get('city', ''),
                    'postal_code': sa.postal_code or order_info.get('postal_code', ''),
                    'phone': sa.phone or order_info.get('phone', ''),
                    'email': sa.email,
                })
                request.session['order_info'] = order_info
                # Also set top-level session fields used by Thawani/order creation
                request.session['customer_name'] = order_info.get('name')
                request.session['customer_email'] = order_info.get('email', request.session.get('customer_email'))
                request.session['customer_phone'] = order_info.get('phone', request.session.get('customer_phone'))
                request.session['address'] = order_info.get('address')
                request.session['city'] = order_info.get('city')
                request.session['postal_code'] = order_info.get('postal_code')
            except (SavedAddress.DoesNotExist, ValueError):
                pass
        # Reset order creation flags for new checkout
        request.session['order_created'] = False
        request.session['thawani_order_created'] = False
        request.session['thawani_order_id'] = None
        return redirect('payment')
    
    return render(request, 'shop/checkout_form.html', {
        'saved_addresses': saved_addresses,
        'categories': categories
    })

def payment(request):
    # Get cart info for total display
    cart = request.session.get('cart', {})
    items = []
    total_price = 0

    for cart_key, quantity in cart.items():
        try:
            if '-' not in cart_key:
                product = Product.objects.get(id=int(cart_key))
                item_total = product.price * quantity
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'total_price': item_total,
                })
                total_price += item_total
            else:
                variant_id, size_id = cart_key.split('-')
                variant_id = int(variant_id)
                size_id = int(size_id)
                variant = ProductVariant.objects.get(id=variant_id)
                size = ProductSize.objects.get(id=int(size_id))
                product = variant.product
                item_total = variant.price * quantity
                items.append({
                    'product': product,
                    'variant': variant,
                    'size': size,
                    'quantity': quantity,
                    'total_price': item_total,
                })
                total_price += item_total
        except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist):
            continue

    # Calculate delivery fee
    from decimal import Decimal
    delivery_fee = Decimal('2.0') if total_price < Decimal('20.0') else Decimal('0.0')
    final_total = total_price + delivery_fee
    
    # Get saved payment methods and categories
    username = request.session.get('username')
    saved_cards = []
    categories = Category.objects.filter(parent__isnull=True)
    
    try:
        user, created = User.objects.get_or_create(username=username)
        saved_cards = SavedPaymentMethod.objects.filter(user=user).order_by('-is_primary', '-created_at')
    except:
        pass
    
    context = {
        'cart': {
            'items': items,
            'total_price': total_price,
            'delivery_fee': delivery_fee,
            'final_total': final_total,
        },
        'saved_cards': saved_cards,
        'categories': categories
    }
    return render(request, 'shop/payment.html', context)

def payment_direct(request):
    """
    Direct payment page without JavaScript
    """
    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, 'Cart is empty')
        return redirect('cart_detail')
    
    # Process cart items for display
    cart_items = []
    total_amount = 0
    
    for cart_key, quantity in cart.items():
        try:
            if '-' not in cart_key:
                # Simple product (no variants)
                product = Product.objects.get(id=int(cart_key))
                item_total = float(product.price) * quantity
                cart_items.append({
                    'product_name': product.name,
                    'price': product.price,
                    'quantity': quantity,
                    'total': item_total
                })
                total_amount += item_total
            else:
                # Product with variants
                variant_id, size_id = cart_key.split('-')
                variant = ProductVariant.objects.get(id=int(variant_id))
                size = ProductSize.objects.get(id=int(size_id))
                product = variant.product
                item_total = float(variant.price) * quantity
                cart_items.append({
                    'product_name': f"{product.name} - {variant.color_name} (Size {size.size})",
                    'price': variant.price,
                    'quantity': quantity,
                    'total': item_total
                })
                total_amount += item_total
        except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist) as e:
            print(f"Error processing cart item {cart_key}: {e}")
            continue
    
    context = {
        'cart_items': cart_items,
        'total_amount': total_amount
    }
    
    return render(request, 'shop/payment_direct.html', context)


def thawani_order_confirmation(request):
    """
    Order confirmation page specifically for Thawani payments
    """
    # Get the most recent order for this session
    from django.db.models import Max
    
    # Try to get order info from session
    order_id = request.session.get('thawani_order_id')
    customer_name = request.session.get('customer_name', 'Guest')
    customer_email = request.session.get('customer_email', 'guest@example.com')
    customer_phone = request.session.get('customer_phone', '+96800000000')
    address = request.session.get('address', '')
    city = request.session.get('city', '')
    postal_code = request.session.get('postal_code', '')
    
    # Try to find the order in database
    order = None
    if order_id:
        try:
            order = Order.objects.get(order_id=order_id)
        except Order.DoesNotExist:
            pass
    
    # If no order found yet, create it from session cart as a final fallback
    if not order and order_id:
        cart = request.session.get('cart', {})
        if cart and not request.session.get('thawani_order_created'):
            try:
                # Calculate total
                total_amount = 0
                for cart_key, quantity in cart.items():
                    if '-' not in cart_key:
                        product = Product.objects.get(id=int(cart_key))
                        total_amount += float(product.price) * quantity
                    else:
                        variant_id, size_id = cart_key.split('-')
                        variant = ProductVariant.objects.get(id=int(variant_id))
                        total_amount += float(variant.price) * quantity
                # Customer info fallbacks
                order_info = request.session.get('order_info', {}) or {}
                customer_name = request.session.get('customer_name') or order_info.get('name', 'Guest')
                customer_email = request.session.get('customer_email') or order_info.get('email', 'guest@example.com')
                customer_phone = request.session.get('customer_phone') or order_info.get('phone') or '+96800000000'
                address = request.session.get('address') or order_info.get('address', '')
                city = request.session.get('city') or order_info.get('city', '')
                postal_code = request.session.get('postal_code') or order_info.get('postal_code', '')
                # Create order
                order = Order.objects.create(
                    order_id=order_id,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    customer_phone=customer_phone,
                    address=address,
                    city=city,
                    postal_code=postal_code,
                    total_amount=total_amount,
                    delivery_fee=Decimal('0.00'),
                    payment_method='Thawani Pay',
                    status='Pending'
                )
                # Items
                for cart_key, quantity in cart.items():
                    try:
                        if '-' not in cart_key:
                            product = Product.objects.get(id=int(cart_key))
                            OrderItem.objects.create(order=order, product_name=product.name, product_id=product.id, quantity=quantity, price=product.price)
                        else:
                            variant_id, size_id = cart_key.split('-')
                            variant = ProductVariant.objects.get(id=int(variant_id))
                            size = ProductSize.objects.get(id=int(size_id))
                            product = variant.product
                            OrderItem.objects.create(order=order, product_name=f"{product.name} - {variant.color_name} (Size {size.size})", product_id=product.id, quantity=quantity, price=variant.price)
                    except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist):
                        continue
                request.session['thawani_order_created'] = True
                request.session['last_order_id'] = order_id
                # Clear cart after creation
                request.session['cart'] = {}
            except Exception:
                pass

    # If still no order, try to get the most recent order
    if not order:
        try:
            order = Order.objects.filter(
                customer_name=customer_name,
                customer_email=customer_email
            ).order_by('-order_date').first()
        except:
            pass
    
    if order:
        # Get order items
        order_items = OrderItem.objects.filter(order=order)
        # Persist for order history page
        request.session['thawani_order_id'] = order.order_id
        request.session['last_order_id'] = order.order_id
        # Ensure cart is cleared after successful payment and mark created
        request.session['cart'] = {}
        request.session['thawani_order_created'] = True
        
        context = {
            'order': order,
            'order_items': order_items,
            'payment_method': 'Thawani Pay',
            'success': True
        }
    else:
        # Fallback if no order found
        context = {
            'order': None,
            'order_items': [],
            'payment_method': 'Thawani Pay',
            'success': True,
            'message': 'Payment successful! Your order has been processed.'
        }
    
    return render(request, 'shop/order_confirmation.html', context)


def order_confirmation(request):
    order_info = request.session.get('order_info')
    # Fallback: allow query parameter to set payment method (e.g., from payment page)
    pm = request.GET.get('pm')
    if pm:
        normalized = pm
        if pm.lower() in ['cod', 'cash', 'cash on delivery']:
            normalized = 'Cash on Delivery'
        request.session['payment_method'] = normalized
    
    # Defensive default: if no gateway payment was used, assume COD
    if not request.session.get('thawani_order_id'):
        current_pm = request.session.get('payment_method')
        if (not current_pm) or (current_pm == 'Credit/Debit Card' and (not pm or pm.lower() in ['cod', 'cash', 'cash on delivery'])):
            request.session['payment_method'] = 'Cash on Delivery'
    
    # Get cart info for display
    cart = request.session.get('cart', {})
    items = []
    total_price = 0

    for cart_key, quantity in cart.items():
        try:
            if '-' not in cart_key:
                product = Product.objects.get(id=int(cart_key))
                item_total = product.price * quantity
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'total_price': item_total,
                })
                total_price += item_total
            else:
                variant_id, size_id = cart_key.split('-')
                variant_id = int(variant_id)
                size_id = int(size_id)
                variant = ProductVariant.objects.get(id=variant_id)
                size = ProductSize.objects.get(id=size_id)
                product = variant.product
                item_total = variant.price * quantity
                items.append({
                    'product': product,
                    'variant': variant,
                    'size': size,
                    'quantity': quantity,
                    'total_price': item_total,
                })
                total_price += item_total
        except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist):
            continue

    # Calculate delivery fee
    from decimal import Decimal
    delivery_fee = Decimal('2.0') if total_price < Decimal('20.0') else Decimal('0.0')
    final_total = total_price + delivery_fee
    
    # Save order to database (only if not already created and no Thawani order exists)
    if order_info and items and not request.session.get('order_created') and not request.session.get('thawani_order_id'):
        import random
        import string
        
        # Generate unique order ID
        import time
        import random
        
        # Create a timestamp-based order ID to ensure uniqueness
        timestamp = int(time.time())
        random_suffix = random.randint(1000, 9999)
        order_id = f"ORD{timestamp}{random_suffix}"
        
        # Ensure the order ID is unique (double-check)
        while Order.objects.filter(order_id=order_id).exists():
            random_suffix = random.randint(1000, 9999)
            order_id = f"ORD{timestamp}{random_suffix}"
        
        # Prepare safe customer details
        safe_customer_name = request.session.get('customer_name') or order_info.get('name', 'Guest')
        safe_customer_email = request.session.get('customer_email') or order_info.get('email', '')
        safe_customer_phone = request.session.get('customer_phone') or order_info.get('phone') or ''
        safe_address = order_info.get('address') or ''
        safe_city = order_info.get('city') or ''
        safe_postal_code = order_info.get('postal_code') or ''

        # Create order
        order = Order.objects.create(
            order_id=order_id,
            customer_name=safe_customer_name,
            customer_email=safe_customer_email,
            customer_phone=safe_customer_phone,
            address=safe_address,
            city=safe_city,
            postal_code=safe_postal_code,
            total_amount=final_total,
            delivery_fee=delivery_fee,
            payment_method=request.session.get('payment_method', 'Credit/Debit Card')
        )
        
        # Create order items
        for item in items:
            OrderItem.objects.create(
                order=order,
                product_name=item['product'].name,
                product_id=item['product'].id,
                quantity=item['quantity'],
                price=item['product'].price
            )
        
        # Mark order as created to prevent duplicates
        request.session['order_created'] = True
    
    context = {
        'order_info': order_info,
        'cart': {
            'items': items,
            'total_price': total_price,
            'delivery_fee': delivery_fee,
            'final_total': final_total,
        },
        'payment_method': request.session.get('payment_method', 'Credit/Debit Card')
    }
    
    # Clear the cart after storing confirmation data
    request.session['cart'] = {}
    request.session['order_created'] = False  # Reset for next order
    request.session['thawani_order_created'] = False  # Reset Thawani order creation flag
    # Keep thawani_order_id so order history can include the most recent Thawani order
    
    return render(request, 'shop/order_confirmation.html', context)


def add_to_cart(request):
    if request.method == 'POST':
        # Get the product_id from the form
        product_id = request.POST.get('product_id')
        
        if not product_id:
            return redirect('home')

        try:
            # Get the product
            product = Product.objects.get(id=product_id)
            
            # Initialize or get the cart from the session
            cart = request.session.get('cart', {})
            
            # Use product_id as the cart key for simple products
            cart_key = str(product_id)
            
            # Increment the quantity if the item is already in the cart
            if cart_key in cart:
                cart[cart_key] += 1
            else:
                cart[cart_key] = 1  # Add new item if it's not in the cart
            
            # Save the updated cart to the session
            request.session['cart'] = cart
            
            # Compute new total quantity for UI update
            new_qty = sum(cart.values())
            
            # If this is an AJAX request, return JSON so the page doesn't navigate
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'cart_quantity': new_qty})
            
            # Non-AJAX: return to product page instead of cart
            try:
                return redirect('product_detail', product_id=int(product_id))
            except Exception:
                return redirect('home')
            
        except Product.DoesNotExist:
            return redirect('home')

    return redirect('home')  # If not POST, redirect to home (fallback)


def remove_from_cart(request, cart_key):
    cart = request.session.get('cart', {})
    if cart_key in cart:
        del cart[cart_key]
        request.session['cart'] = cart
    return redirect('cart_detail')


@require_POST
def update_cart_quantity(request, cart_key):
    cart = request.session.get('cart', {})
    try:
        quantity = int(request.POST.get('quantity', 1))
        if quantity > 0:
            cart[cart_key] = quantity
        else:
            cart.pop(cart_key, None)  # Remove if quantity is zero or less
        request.session['cart'] = cart
    except (ValueError, TypeError):
        pass  # Ignore invalid input
    return redirect('cart_detail')


def product_detail(request, product_id):
    print(f"DEBUG: product_detail called with product_id: {product_id}")  # Debug print
    product = get_object_or_404(Product, id=product_id)
    print(f"DEBUG: Found product: {product.name}")  # Debug print
    variants = product.variants.all()
    print(f"DEBUG: Found {variants.count()} variants")  # Debug print
    
    # Get all top-level categories for navigation
    categories = Category.objects.filter(parent__isnull=True)
    
    # Process specifications for template
    specifications = []
    if product.specifications:
        for line in product.specifications.splitlines():
            line = line.strip()
            if line and ':' in line:
                parts = line.split(':', 1)  # Split only on first colon
                if len(parts) == 2:
                    specifications.append({
                        'label': parts[0].strip(),
                        'value': parts[1].strip()
                    })
    
    context = {
        'product': product,
        'variants': variants,
        'categories': categories,
        'specifications': specifications
    }
    print(f"DEBUG: Rendering template with context: {context}")  # Debug print
    return render(request, 'shop/product_detail.html', context)

def add_product(request):
    if request.method == 'POST':
        form = AddProductForm(request.POST)
        if form.is_valid():
            product = form.save()
            return redirect('product_detail', product_id=product.id)
    else:
        form = AddProductForm()
    
    # Get all categories for the dropdown
    categories = Category.objects.all()
    
    return render(request, 'shop/add_product.html', {
        'form': form,
        'categories': categories
    })

def edit_product(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
        if request.method == 'POST':
            # Handle delete action
            if request.POST.get('action') == 'delete':
                product.delete()
                return redirect('all_products')
            form = EditProductForm(request.POST, instance=product)
            if form.is_valid():
                form.save()
                return redirect('product_detail', product_id=product.id)
        else:
            form = EditProductForm(instance=product)

        # Get all categories for the dropdown
        categories = Category.objects.all()

        return render(request, 'shop/edit_product.html', {
            'form': form, 
            'product': product,
            'categories': categories
        })
    except Product.DoesNotExist:
        return redirect('home')


def search_products(request):
    query = request.GET.get('q', '')
    products = []
    
    if query:
        # Search in product name and description
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        ).distinct()
    
    context = {
        'products': products,
        'query': query,
    }
    return render(request, 'shop/search_results.html', context)


def all_products(request):
    # Show all products
    products = Product.objects.all()
    # Get all top-level categories for navigation
    categories = Category.objects.filter(parent__isnull=True)
    return render(request, 'shop/all_products.html', {'products': products, 'categories': categories})


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Check if it's admin login
        if username == 'admin' and password == '123':
            # Set admin session
            request.session['is_admin'] = True
            request.session['admin_username'] = username
            request.session['username'] = username  # Also set regular username for admin
            
            # Check if there's a next_url to redirect to
            next_url = request.session.get('next_url')
            if next_url:
                del request.session['next_url']  # Clear the stored URL
                return redirect(next_url)
            return redirect('home')
        else:
            # Check if user exists in database
            try:
                user = User.objects.get(username=username, password=password)
                request.session['is_logged_in'] = True
                request.session['username'] = username
                # Ensure checkout/order association picks up user identity
                request.session['customer_name'] = username
                if getattr(user, 'email', None):
                    request.session['customer_email'] = user.email
                if getattr(user, 'phone', None):
                    request.session['customer_phone'] = user.phone
                
                # Check if there's a next_url to redirect to
                next_url = request.session.get('next_url')
                if next_url:
                    del request.session['next_url']  # Clear the stored URL
                    return redirect(next_url)
                return redirect('home')
            except User.DoesNotExist:
                # User doesn't exist, show error
                return render(request, 'shop/login.html', {
                    'error_message': 'Invalid username or password'
                })
    
    # Check if user was redirected from checkout
    checkout_required = request.session.get('next_url') == 'checkout'
    
    return render(request, 'shop/login.html', {
        'checkout_required': checkout_required
    })


def signup_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Check if username already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'shop/signup.html', {
                'error_message': 'Username already exists. Please choose a different username.'
            })
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return render(request, 'shop/signup.html', {
                'error_message': 'Email already exists. Please use a different email.'
            })
        
        # Create new user
        user = User.objects.create(
            username=username,
            email=email,
            password=password
        )
        
        # Log the user in automatically
        request.session['is_logged_in'] = True
        request.session['username'] = username
        # Persist identity for order association
        request.session['customer_name'] = username
        if getattr(user, 'email', None):
            request.session['customer_email'] = user.email
        
        # Check if there's a next_url to redirect to
        next_url = request.session.get('next_url')
        if next_url:
            del request.session['next_url']  # Clear the stored URL
            return redirect(next_url)
        return redirect('home')
    
    # Check if user was redirected from checkout
    checkout_required = request.session.get('next_url') == 'checkout'
    
    return render(request, 'shop/signup.html', {
        'checkout_required': checkout_required
    })


def logout_view(request):
    # Clear all session data
    request.session.flush()
    return redirect('home')



def orders_database(request):
    # Check if user is admin
    if not request.session.get('is_admin'):
        return redirect('home')
    
    # Get real orders from database
    orders = Order.objects.all().order_by('-order_date')
    
    return render(request, 'shop/orders_database.html', {'orders': orders})


def order_history(request):
    # Check if user is logged in
    if not request.session.get('is_logged_in') and not request.session.get('is_admin'):
        return redirect('login')
    
    # Get the username from session
    username = request.session.get('username')
    customer_email = request.session.get('customer_email')
    customer_phone = request.session.get('customer_phone')
    thawani_order_id = request.session.get('thawani_order_id') or request.session.get('last_order_id')

    # Build a flexible filter since we don't have a FK to User
    from django.db.models import Q
    query = Q()
    if username:
        query |= Q(customer_name__icontains=username)
        # some sites use email as username
        query |= Q(customer_email__icontains=username)
    if customer_email:
        query |= Q(customer_email__iexact=customer_email)
    if customer_phone:
        query |= Q(customer_phone__iexact=customer_phone)

    orders = Order.objects.filter(query).order_by('-order_date') if query else Order.objects.none()

    # Always include the most recent order created in this session (e.g., via Thawani)
    if thawani_order_id:
        try:
            recent = Order.objects.filter(order_id=thawani_order_id)
            orders = (orders | recent).distinct().order_by('-order_date')
        except Order.DoesNotExist:
            pass
    
    # Fallbacks to ensure the user sees something even if identity fields didn't match
    if not orders.exists():
        from django.utils import timezone
        from datetime import timedelta
        since = timezone.now() - timedelta(days=1)
        # Include recent orders and any recent Thawani orders
        recent_time = Order.objects.filter(order_date__gte=since)
        recent_thawani = Order.objects.filter(order_date__gte=since, payment_method__icontains='thawani')
        orders = (recent_time | recent_thawani).distinct().order_by('-order_date')
    if not orders.exists():
        orders = Order.objects.all().order_by('-order_date')[:20]
    
    # Get all top-level categories for navigation
    categories = Category.objects.filter(parent__isnull=True)
    
    # Get saved addresses and payment methods
    try:
        user, created = User.objects.get_or_create(username=username)
        saved_addresses = SavedAddress.objects.filter(user=user).order_by('-is_primary', '-created_at')
        saved_cards = SavedPaymentMethod.objects.filter(user=user).order_by('-is_primary', '-created_at')
    except:
        saved_addresses = []
        saved_cards = []
    
    return render(request, 'shop/order_history.html', {
        'orders': orders,
        'categories': categories,
        'username': username,
        'saved_addresses': saved_addresses,
        'saved_cards': saved_cards
    })


def update_order_status(request, order_id):
    # Check if user is admin
    if not request.session.get('is_admin'):
        print(f"DEBUG: User not admin, redirecting to home")
        return redirect('home')
    
    print(f"DEBUG: update_order_status called for order_id={order_id}, method={request.method}")
    
    if request.method == 'POST':
        order = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        
        print(f"DEBUG: Order found: {order.order_id}, new_status: {new_status}")
        
        # Validate status
        valid_statuses = ['Pending', 'Shipped', 'Delivered']
        if new_status in valid_statuses:
            print(f"DEBUG: Status valid, updating order status from {order.status} to {new_status}")
            order.status = new_status
            order.save()
            print(f"DEBUG: Order saved successfully")
            
            # Return JSON response for AJAX requests
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'success': True, 'status': new_status})
            
            # Redirect back to orders database
            return redirect('orders_database')
        else:
            print(f"DEBUG: Invalid status: {new_status}")
    else:
        print(f"DEBUG: Not a POST request, method: {request.method}")
    
    return redirect('orders_database')


# Thawani Pay Integration Views
@csrf_exempt
def thawani_create_session(request):
    """
    Create a Thawani Pay checkout session with robust error handling
    """
    if request.method == 'POST':
        print("=== Thawani Create Session Started ===")
        
        try:
            # Get cart data from session
            cart = request.session.get('cart', {})
            if not cart:
                return JsonResponse({
                    'success': False,
                    'error': 'Cart is empty'
                })
            
            print(f"Cart data: {cart}")
            
            # Generate unique order ID
            import random
            import string
            order_id = 'THW' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Process cart items to get product details
            items = []
            total_amount = 0
            
            for cart_key, quantity in cart.items():
                try:
                    if '-' not in cart_key:
                        # Simple product (no variants)
                        product = Product.objects.get(id=int(cart_key))
                        item_total = float(product.price) * quantity
                        items.append({
                            'product_name': product.name,
                            'price': float(product.price),
                            'quantity': quantity
                        })
                        total_amount += item_total
                    else:
                        # Product with variants
                        variant_id, size_id = cart_key.split('-')
                        variant = ProductVariant.objects.get(id=int(variant_id))
                        size = ProductSize.objects.get(id=int(size_id))
                        product = variant.product
                        item_total = float(variant.price) * quantity
                        items.append({
                            'product_name': f"{product.name} - {variant.color_name} (Size {size.size})",
                            'price': float(variant.price),
                            'quantity': quantity
                        })
                        total_amount += item_total
                except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist) as e:
                    print(f"Error processing cart item {cart_key}: {e}")
                    continue  # Skip invalid items
            
            if not items:
                return JsonResponse({
                    'success': False,
                    'error': 'No valid items in cart'
                })
            
            print(f"Processed items: {items}")
            print(f"Total amount: {total_amount}")
            
            # Prepare order data
            order_data = {
                'order_id': order_id,
                'total_amount': total_amount,
                'items': items
            }
            
            # Prepare customer info (you might want to get this from user profile or form)
            customer_info = {
                'name': 'Customer',  # You can get this from user profile
                'email': 'customer@example.com',  # You can get this from user profile
                'phone': '+96812345678'  # You can get this from user profile
            }
            
            print(f"Order data: {order_data}")
            print(f"Customer info: {customer_info}")
            
            # Create Thawani service instance
            thawani_service = ThawaniPayService()
            
            print("Calling Thawani API...")
            result = thawani_service.create_checkout_session(order_data, customer_info)
            print(f"Thawani API result: {result}")
            print(f"Result type: {type(result)}")
            print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
            
            if result['success']:
                # Store session info in Django session
                request.session['thawani_session_id'] = result['session_id']
                request.session['thawani_order_id'] = order_id
                
                print(f"Session created successfully!")
                print(f"Session ID: {result['session_id']}")
                print(f"Checkout URL: {result['checkout_url']}")
                
                return JsonResponse({
                    'success': True,
                    'checkout_url': result['checkout_url'],
                    'session_id': result['session_id']
                })
            else:
                print(f"Thawani API error: {result['error']}")
                
                # Provide user-friendly error messages
                error_message = result['error']
                if 'All API endpoints failed' in error_message:
                    error_message = 'Payment service is temporarily unavailable. Please try again in a few minutes.'
                elif '404' in error_message:
                    error_message = 'Payment service temporarily unavailable. Please try again in a few minutes.'
                elif 'timeout' in error_message.lower():
                    error_message = 'Payment service is slow to respond. Please try again.'
                elif 'connection' in error_message.lower():
                    error_message = 'Cannot connect to payment service. Please check your internet connection.'
                
                return JsonResponse({
                    'success': False,
                    'error': error_message
                })
                
        except Exception as e:
            print(f"Exception in thawani_create_session: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Internal server error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

def thawani_payment_direct(request):
    """
    Robust Python-based Thawani payment without JavaScript
    """
    if request.method == 'POST':
        try:
            # Get cart data from session
            cart = request.session.get('cart', {})
            if not cart:
                messages.error(request, 'Cart is empty')
                return redirect('cart_detail')
            
            # Generate unique order ID
            import random
            import string
            order_id = 'THW' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Process cart items to get product details
            items = []
            total_amount = 0
            
            for cart_key, quantity in cart.items():
                try:
                    if '-' not in cart_key:
                        # Simple product (no variants)
                        product = Product.objects.get(id=int(cart_key))
                        item_total = float(product.price) * quantity
                        items.append({
                            'product_name': product.name,
                            'price': float(product.price),
                            'quantity': quantity
                        })
                        total_amount += item_total
                    else:
                        # Product with variants
                        variant_id, size_id = cart_key.split('-')
                        variant = ProductVariant.objects.get(id=int(variant_id))
                        size = ProductSize.objects.get(id=int(size_id))
                        product = variant.product
                        item_total = float(variant.price) * quantity
                        items.append({
                            'product_name': f"{product.name} - {variant.color_name} (Size {size.size})",
                            'price': float(variant.price),
                            'quantity': quantity
                        })
                        total_amount += item_total
                except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist) as e:
                    print(f"Error processing cart item {cart_key}: {e}")
                    continue
            
            if not items:
                messages.error(request, 'No valid items in cart')
                return redirect('cart_detail')
            
            # Prepare order data
            order_data = {
                'order_id': order_id,
                'total_amount': total_amount,
                'items': items
            }
            
            # Prepare customer info
            customer_info = {
                'name': 'Customer',
                'email': 'customer@example.com',
                'phone': '+96812345678'
            }
            
            # Create Thawani service instance
            thawani_service = ThawaniPayService()
            
            # Create checkout session with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"Thawani API attempt {attempt + 1}/{max_retries}")
                    result = thawani_service.create_checkout_session(order_data, customer_info)
                    
                    if result['success']:
                        # Store session info in Django session
                        request.session['thawani_session_id'] = result['session_id']
                        request.session['thawani_order_id'] = order_id
                        
                        # Redirect directly to Thawani checkout
                        checkout_url = result['checkout_url']
                        print(f"Redirecting to Thawani: {checkout_url}")
                        
                        # Add a small delay to ensure session is ready
                        import time
                        time.sleep(1)
                        
                        return redirect(checkout_url)
                    else:
                        print(f"Thawani API error (attempt {attempt + 1}): {result['error']}")
                        if attempt == max_retries - 1:
                            messages.error(request, f'Payment error: {result["error"]}')
                            return redirect('payment_direct')
                        time.sleep(2)  # Wait before retry
                        
                except Exception as e:
                    print(f"Exception in Thawani API call (attempt {attempt + 1}): {str(e)}")
                    if attempt == max_retries - 1:
                        messages.error(request, f'Payment service temporarily unavailable. Please try again.')
                        return redirect('payment_direct')
                    time.sleep(2)  # Wait before retry
            
            messages.error(request, 'Payment service is currently unavailable. Please try again later.')
            return redirect('payment_direct')
                
        except Exception as e:
            print(f"Exception in thawani_payment_direct: {str(e)}")
            messages.error(request, 'An unexpected error occurred. Please try again.')
            return redirect('payment_direct')
    
    # If not POST, redirect to payment page
    return redirect('payment_direct')


def clear_cart(request):
    """
    Clear the cart for debugging purposes
    """
    if request.method == 'POST':
        request.session['cart'] = {}
        request.session['order_created'] = False  # Reset order creation flag
        request.session['thawani_order_created'] = False  # Reset Thawani order creation flag
        request.session['thawani_order_id'] = None  # Reset Thawani order ID
        return JsonResponse({'success': True, 'message': 'Cart cleared'})
    return JsonResponse({'success': False, 'error': 'Invalid method'})


def debug_thawani_page(request):
    """
    Debug page for testing Thawani payment flow
    """
    return render(request, 'shop/debug_thawani.html')


def debug_thawani_session(request):
    """
    Debug endpoint to test Thawani session creation
    """
    if request.method == 'POST':
        try:
            # Get cart data from session
            cart = request.session.get('cart', {})
            print(f"Debug: Cart data: {cart}")
            
            if not cart:
                return JsonResponse({
                    'success': False,
                    'error': 'Cart is empty'
                })
            
            # Generate unique order ID
            import random
            import string
            order_id = 'DEBUG_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            
            # Process cart items
            items = []
            total_amount = 0
            
            for cart_key, quantity in cart.items():
                try:
                    if '-' not in cart_key:
                        product = Product.objects.get(id=int(cart_key))
                        item_total = float(product.price) * quantity
                        items.append({
                            'product_name': product.name,
                            'price': float(product.price),
                            'quantity': quantity
                        })
                        total_amount += item_total
                    else:
                        variant_id, size_id = cart_key.split('-')
                        variant = ProductVariant.objects.get(id=int(variant_id))
                        size = ProductSize.objects.get(id=int(size_id))
                        product = variant.product
                        item_total = float(variant.price) * quantity
                        items.append({
                            'product_name': f"{product.name} - {variant.color_name} (Size {size.size})",
                            'price': float(variant.price),
                            'quantity': quantity
                        })
                        total_amount += item_total
                except Exception as e:
                    print(f"Debug: Error processing item {cart_key}: {e}")
                    continue
            
            print(f"Debug: Processed items: {items}")
            print(f"Debug: Total amount: {total_amount}")
            
            # Create order data
            order_data = {
                'order_id': order_id,
                'total_amount': total_amount,
                'items': items
            }
            
            customer_info = {
                'name': 'Debug Customer',
                'email': 'debug@example.com',
                'phone': '+96812345678'
            }
            
            # Create Thawani service instance
            thawani_service = ThawaniPayService()
            
            print("Debug: Calling Thawani API...")
            result = thawani_service.create_checkout_session(order_data, customer_info)
            print(f"Debug: Thawani API result: {result}")
            
            if result['success']:
                # Store session info
                request.session['thawani_session_id'] = result['session_id']
                request.session['thawani_order_id'] = order_id
                
                return JsonResponse({
                    'success': True,
                    'checkout_url': result['checkout_url'],
                    'session_id': result['session_id'],
                    'debug_info': {
                        'order_id': order_id,
                        'total_amount': total_amount,
                        'items_count': len(items),
                        'cart_items': list(cart.keys())
                    }
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'debug_info': {
                        'order_id': order_id,
                        'total_amount': total_amount,
                        'items_count': len(items)
                    }
                })
                
        except Exception as e:
            print(f"Debug: Exception: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Exception: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })


def test_thawani_success(request):
    """
    Test endpoint to verify Thawani success URL is being called
    """
    print("=== Test Thawani Success Endpoint Called ===")
    print(f"Request method: {request.method}")
    print(f"Request path: {request.path}")
    print(f"All GET parameters: {request.GET}")
    print(f"All POST parameters: {request.POST}")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Session data: {dict(request.session)}")
    
    # Return a simple success page for testing
    return render(request, 'shop/test.html', {
        'message': 'Thawani success endpoint was called successfully!',
        'session_id': request.GET.get('session_id', 'No session ID'),
        'all_params': dict(request.GET)
    })


def simple_test_view(request):
    """
    Simple test view for debugging
    """
    return render(request, 'shop/simple_test.html')


def test_thawani_flow(request):
    """
    Simple test to verify Thawani flow is working
    """
    print("=== Test Thawani Flow ===")
    
    # Add some test items to cart
    request.session['cart'] = {'1': 2, '2': 1}  # Add some test items
    
    # Create a test order
    import random
    import string
    order_id = 'TEST_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    # Create Thawani service
    thawani_service = ThawaniPayService()
    
    # Test order data
    order_data = {
        'order_id': order_id,
        'total_amount': 50.0,
        'items': [
            {'product_name': 'Test Product 1', 'price': 25.0, 'quantity': 2}
        ]
    }
    
    customer_info = {
        'name': 'Test Customer',
        'email': 'test@example.com',
        'phone': '+96812345678'
    }
    
    print(f"Creating test session with order_id: {order_id}")
    result = thawani_service.create_checkout_session(order_data, customer_info)
    print(f"Thawani result: {result}")
    
    if result['success']:
        # Store session info
        request.session['thawani_session_id'] = result['session_id']
        request.session['thawani_order_id'] = order_id
        
        return JsonResponse({
            'success': True,
            'checkout_url': result['checkout_url'],
            'session_id': result['session_id'],
            'message': 'Test session created successfully'
        })
    else:
        return JsonResponse({
            'success': False,
            'error': result.get('error', 'Unknown error')
        })


def thawani_success(request):
    """
    Handle successful payment from Thawani
    """
    # Immediately send the customer to the confirmation page.
    # The confirmation view already knows how to read session data,
    # finalize the order if needed, and show the success screen.
    return redirect('thawani_order_confirmation')
    
    # Try to get session_id from various sources
    session_id = request.GET.get('session_id') or request.POST.get('session_id')
    print(f"Session ID from request: {session_id}")
    
    # Check if session_id is in the URL path (Thawani might include it there)
    if not session_id:
        path_parts = request.path.split('/')
        for part in path_parts:
            if part.startswith('checkout_'):
                session_id = part
                print(f"Found session ID in URL path: {session_id}")
                break
    
    # Also check for session_id in query parameters with different names
    if not session_id:
        session_id = request.GET.get('session') or request.GET.get('id') or request.GET.get('payment_id')
        if session_id:
            print(f"Found session ID in alternative parameters: {session_id}")
    
    # If no session_id in request, try to get it from stored session data
    if not session_id:
        stored_session_id = request.session.get('thawani_session_id')
        print(f"Stored session ID: {stored_session_id}")
        if stored_session_id:
            session_id = stored_session_id
            print(f"Using stored session ID: {session_id}")
        else:
            print("No stored session ID found")
    
    # If still no session_id, check if we have cart data and create order anyway
    if not session_id:
        cart = request.session.get('cart', {})
        if cart:
            print("No session ID but cart exists - creating order from cart data")
            # This will be handled in the fallback section below
        else:
            print("No session ID and no cart data")
    
    # For testing: if we have a session_id in the URL, use it
    if not session_id and 'test_session' in request.GET:
        session_id = request.GET.get('test_session')
        print(f"Using test session ID: {session_id}")
    
    # For testing: if we have a direct session_id parameter, use it
    if not session_id and 'session_id' in request.GET:
        session_id = request.GET.get('session_id')
        print(f"Using direct session_id parameter: {session_id}")
    
    if session_id:
        # Check if this is a mock session
        if session_id.startswith('MOCK_'):
            print(f"Processing mock session: {session_id}")
            # Handle mock session directly
            try:
                cart = request.session.get('cart', {})
                if cart:
                    # Calculate total from cart
                    total_amount = 0
                    for cart_key, quantity in cart.items():
                        try:
                            if '-' not in cart_key:
                                product = Product.objects.get(id=int(cart_key))
                                total_amount += float(product.price) * quantity
                            else:
                                variant_id, size_id = cart_key.split('-')
                                variant = ProductVariant.objects.get(id=int(variant_id))
                                total_amount += float(variant.price) * quantity
                        except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist):
                            continue
                    
                    # Create order for mock payment (only if not already created)
                    if not request.session.get('thawani_order_created'):
                        order = Order.objects.create(
                        order_id=session_id,
                        customer_name='Mock Customer',
                        customer_email='mock@example.com',
                        customer_phone='+96812345678',
                        address='Mock Address',
                        city='Mock City',
                        postal_code='12345',
                        total_amount=total_amount,
                        delivery_fee=Decimal('0.00'),
                        payment_method='Thawani Pay (Mock)',
                        status='Pending'
                        )
                        
                        # Store order ID in session for confirmation page
                        request.session['thawani_order_id'] = session_id
                        request.session['thawani_order_created'] = True
                        
                        # Create order items
                        for cart_key, quantity in cart.items():
                            try:
                                if '-' not in cart_key:
                                    product = Product.objects.get(id=int(cart_key))
                                    OrderItem.objects.create(
                                        order=order,
                                        product_name=product.name,
                                        product_id=product.id,
                                        quantity=quantity,
                                        price=product.price
                                    )
                                else:
                                    variant_id, size_id = cart_key.split('-')
                                    variant = ProductVariant.objects.get(id=int(variant_id))
                                    size = ProductSize.objects.get(id=int(size_id))
                                    product = variant.product
                                    OrderItem.objects.create(
                                        order=order,
                                        product_name=f"{product.name} - {variant.color_name} (Size {size.size})",
                                        product_id=product.id,
                                        quantity=quantity,
                                        price=variant.price
                                    )
                            except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist):
                                continue
                        
                        # Clear cart
                        request.session['cart'] = {}
                        
                        messages.success(request, f'Mock payment successful! Order #{order.order_id}')
                        return redirect('thawani_order_confirmation')
                    else:
                        # Order already created, just redirect
                        messages.success(request, f'Mock payment successful! Order already created.')
                        return redirect('thawani_order_confirmation')
            
            except Exception as e:
                print(f"Error processing mock payment: {str(e)}")
                messages.error(request, 'Error processing mock payment.')
                return redirect('cart_detail')
        
        # Verify payment with Thawani
        thawani_service = ThawaniPayService()
        session_status = thawani_service.get_session_status(session_id)
        print(f"Session status: {session_status}")
        
        if session_status['success']:
            data = session_status['data']
            print(f"Session data: {data}")
            if data.get('payment_status') == 'paid':
                # Payment successful - create order
                try:
                    cart = request.session.get('cart', {})
                    if cart:
                        # Calculate total from cart
                        total_amount = 0
                        for cart_key, quantity in cart.items():
                            try:
                                if '-' not in cart_key:
                                    product = Product.objects.get(id=int(cart_key))
                                    total_amount += float(product.price) * quantity
                                else:
                                    variant_id, size_id = cart_key.split('-')
                                    variant = ProductVariant.objects.get(id=int(variant_id))
                                    total_amount += float(variant.price) * quantity
                            except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist):
                                continue
                        
                        # Create order (only if not already created)
                        if not request.session.get('thawani_order_created'):
                            order_id = request.session.get('thawani_order_id', 'THW' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)))
                            order_info = request.session.get('order_info', {}) or {}
                            customer_name = request.session.get('customer_name') or order_info.get('name', 'Guest')
                            customer_email = request.session.get('customer_email') or order_info.get('email', 'guest@example.com')
                            customer_phone = request.session.get('customer_phone') or order_info.get('phone') or '+96800000000'
                            address = request.session.get('address') or order_info.get('address', '')
                            city = request.session.get('city') or order_info.get('city', '')
                            postal_code = request.session.get('postal_code') or order_info.get('postal_code', '')

                            order = Order.objects.create(
                                order_id=order_id,
                                customer_name=customer_name,
                                customer_email=customer_email,
                                customer_phone=customer_phone,
                                address=address,
                                city=city,
                                postal_code=postal_code,
                                total_amount=total_amount,
                                delivery_fee=Decimal('0.00'),
                                payment_method='Thawani Pay',
                                status='Pending'
                            )
                        
                            # Store order ID in session for confirmation page
                            request.session['thawani_order_id'] = order_id
                            request.session['last_order_id'] = order_id
                            request.session['thawani_order_created'] = True
                        
                            # Create order items
                            for cart_key, quantity in cart.items():
                                try:
                                    if '-' not in cart_key:
                                        product = Product.objects.get(id=int(cart_key))
                                        OrderItem.objects.create(
                                            order=order,
                                            product_name=product.name,
                                            product_id=product.id,
                                            quantity=quantity,
                                            price=product.price
                                        )
                                    else:
                                        variant_id, size_id = cart_key.split('-')
                                        variant = ProductVariant.objects.get(id=int(variant_id))
                                        size = ProductSize.objects.get(id=int(size_id))
                                        product = variant.product
                                        OrderItem.objects.create(
                                            order=order,
                                            product_name=f"{product.name} - {variant.color_name} (Size {size.size})",
                                            product_id=product.id,
                                            quantity=quantity,
                                            price=variant.price
                                        )
                                except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist):
                                    continue
                        
                            # Clear cart
                            request.session['cart'] = {}
                            
                            messages.success(request, 'Payment successful! Your order has been placed.')
                            return redirect('thawani_order_confirmation')
                        else:
                            # Order already created, just redirect
                            messages.success(request, 'Payment successful! Your order has been placed.')
                            return redirect('thawani_order_confirmation')
                
                except Exception as e:
                    print(f"Error processing payment: {str(e)}")
                    messages.error(request, f'Error processing payment: {str(e)}')
                    return redirect('cart_detail')
            else:
                print(f"Payment status not paid: {data.get('payment_status')}")
                messages.error(request, 'Payment was not completed successfully.')
                return redirect('cart_detail')
        else:
            print(f"Session verification failed: {session_status.get('error', 'Unknown error')}")
            messages.error(request, 'Could not verify payment status.')
            return redirect('cart_detail')
    else:
        print("No session ID provided")
        
        # Check if we have cart data and can create a mock session
        cart = request.session.get('cart', {})
        print(f"Cart data: {cart}")
        if cart:
            print("Creating mock session from cart data")
            try:
                # Calculate total from cart
                total_amount = 0
                for cart_key, quantity in cart.items():
                    try:
                        if '-' not in cart_key:
                            product = Product.objects.get(id=int(cart_key))
                            total_amount += float(product.price) * quantity
                        else:
                            variant_id, size_id = cart_key.split('-')
                            variant = ProductVariant.objects.get(id=int(variant_id))
                            total_amount += float(variant.price) * quantity
                    except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist):
                        continue
                
                if total_amount > 0:
                    # Create order for successful payment
                    import random
                    import string
                    mock_session_id = 'MOCK_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
                    
                    order_info = request.session.get('order_info', {}) or {}
                    customer_name = request.session.get('customer_name') or order_info.get('name', 'Guest')
                    customer_email = request.session.get('customer_email') or order_info.get('email', 'guest@example.com')
                    customer_phone = request.session.get('customer_phone') or order_info.get('phone') or '+96800000000'
                    address = request.session.get('address') or order_info.get('address', '')
                    city = request.session.get('city') or order_info.get('city', '')
                    postal_code = request.session.get('postal_code') or order_info.get('postal_code', '')

                    order = Order.objects.create(
                        order_id=mock_session_id,
                        customer_name=customer_name,
                        customer_email=customer_email,
                        customer_phone=customer_phone,
                        address=address,
                        city=city,
                        postal_code=postal_code,
                        total_amount=total_amount,
                        delivery_fee=Decimal('0.00'),
                        payment_method='Thawani Pay',
                        status='Pending'
                    )
                    request.session['last_order_id'] = mock_session_id
                    
                    # Create order items
                    for cart_key, quantity in cart.items():
                        try:
                            if '-' not in cart_key:
                                product = Product.objects.get(id=int(cart_key))
                                OrderItem.objects.create(
                                    order=order,
                                    product_name=product.name,
                                    product_id=product.id,
                                    quantity=quantity,
                                    price=product.price
                                )
                            else:
                                variant_id, size_id = cart_key.split('-')
                                variant = ProductVariant.objects.get(id=int(variant_id))
                                size = ProductSize.objects.get(id=int(size_id))
                                product = variant.product
                                OrderItem.objects.create(
                                    order=order,
                                    product_name=f"{product.name} - {variant.color_name} (Size {size.size})",
                                    product_id=product.id,
                                    quantity=quantity,
                                    price=variant.price
                                )
                        except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist):
                            continue
                    
                    # Clear cart
                    request.session['cart'] = {}
                    
                    messages.success(request, f'Payment successful! Order #{order.order_id}')
                    return redirect('order_confirmation')
            
            except Exception as e:
                print(f"Error creating mock order: {str(e)}")
        
        messages.error(request, 'No session ID provided.')
    
    print("Redirecting to cart page due to missing session ID")
    return redirect('cart_detail')


def thawani_cancel(request):
    """
    Handle cancelled payment from Thawani
    """
    messages.warning(request, 'Payment was cancelled. You can try again.')
    return redirect('payment')

def thawani_mock_success(request):
    """
    Handle mock successful payment when Thawani is down
    """
    session_id = request.GET.get('session_id')
    
    if session_id and session_id.startswith('MOCK_'):
        # Create order for mock payment
        try:
            cart = request.session.get('cart', {})
            if cart:
                # Calculate total from cart
                total_amount = 0
                items = []
                
                for cart_key, quantity in cart.items():
                    try:
                        if '-' not in cart_key:
                            # Simple product (no variants)
                            product = Product.objects.get(id=int(cart_key))
                            item_total = float(product.price) * quantity
                            items.append({
                                'product_name': product.name,
                                'price': float(product.price),
                                'quantity': quantity
                            })
                            total_amount += item_total
                        else:
                            # Product with variants
                            variant_id, size_id = cart_key.split('-')
                            variant = ProductVariant.objects.get(id=int(variant_id))
                            size = ProductSize.objects.get(id=int(size_id))
                            product = variant.product
                            item_total = float(variant.price) * quantity
                            items.append({
                                'product_name': f"{product.name} - {variant.color_name} (Size {size.size})",
                                'price': float(variant.price),
                                'quantity': quantity
                            })
                            total_amount += item_total
                    except (ValueError, Product.DoesNotExist, ProductVariant.DoesNotExist, ProductSize.DoesNotExist) as e:
                        continue
                
                if items:
                    # Create order
                    order = Order.objects.create(
                        order_id=session_id,
                        customer_name='Mock Customer',
                        customer_email='mock@example.com',
                        customer_phone='+96812345678',
                        address='Mock Address',
                        city='Mock City',
                        postal_code='12345',
                        total_amount=total_amount,
                        delivery_fee=Decimal('0.00'),
                        payment_method='Thawani Pay (Mock)',
                        status='Pending'
                    )
                    
                    # Store order ID in session for confirmation page
                    request.session['thawani_order_id'] = session_id
                    
                    # Create order items
                    for item in items:
                        OrderItem.objects.create(
                            order=order,
                            product_name=item['product_name'],
                            product_id=1,  # Default product ID for mock orders
                            quantity=item['quantity'],
                            price=item['price']
                        )
                    
                    # Clear cart
                    request.session['cart'] = {}
                    
                    messages.success(request, f'Mock payment successful! Order #{order.order_id}')
                    return redirect('thawani_order_confirmation')
        
        except Exception as e:
            print(f"Error processing mock payment: {str(e)}")
            messages.error(request, 'Error processing mock payment.')
            return redirect('cart_detail')
    
    messages.error(request, 'Invalid mock session.')
    return redirect('cart_detail')


@csrf_exempt
def thawani_webhook(request):
    """
    Handle webhooks from Thawani Pay
    """
    if request.method == 'POST':
        try:
            # Get webhook headers
            timestamp = request.headers.get('thawani-timestamp')
            signature = request.headers.get('thawani-signature')
            
            if not timestamp or not signature:
                return JsonResponse({'error': 'Missing webhook headers'}, status=400)
            
            # Get webhook body
            body = request.body.decode('utf-8')
            
            # Verify webhook signature
            thawani_service = ThawaniPayService()
            if not thawani_service.verify_webhook_signature(body, timestamp, signature):
                return JsonResponse({'error': 'Invalid webhook signature'}, status=400)
            
            # Parse webhook data
            webhook_data = json.loads(body)
            event_type = webhook_data.get('event_type')
            data = webhook_data.get('data', {})
            
            # Handle different event types
            if event_type == 'checkout.completed':
                # Payment completed successfully
                client_reference_id = data.get('client_reference_id')
                if client_reference_id:
                    try:
                        order = Order.objects.get(order_id=client_reference_id)
                        order.status = 'Paid'
                        order.save()
                    except Order.DoesNotExist:
                        pass  # Order not found
                        
            elif event_type == 'payment.succeeded':
                # Payment succeeded
                checkout_invoice = data.get('checkout_invoice')
                if checkout_invoice:
                    try:
                        order = Order.objects.get(order_id=checkout_invoice)
                        order.status = 'Paid'
                        order.save()
                    except Order.DoesNotExist:
                        pass  # Order not found
                        
            elif event_type == 'payment.failed':
                # Payment failed
                checkout_invoice = data.get('checkout_invoice')
                if checkout_invoice:
                    try:
                        order = Order.objects.get(order_id=checkout_invoice)
                        order.status = 'Failed'
                        order.save()
                    except Order.DoesNotExist:
                        pass  # Order not found
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({'error': f'Webhook processing error: {str(e)}'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


def contact(request):
    """
    Contact page view
    """
    if request.method == 'POST':
        # Handle form submission here if needed
        # For now, just render the page
        pass
    
    return render(request, 'shop/contact.html')


def save_address_info(request):
    """
    Save or update user's shipping address
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            # Get user from session (you might want to use proper user authentication)
            username = request.session.get('username', 'default_user')
            user, created = User.objects.get_or_create(username=username)
            
            if action == 'add':
                # Create new address
                address = SavedAddress.objects.create(
                    user=user,
                    name=data['name'],
                    email=data['email'],
                    phone=data['phone'],
                    address=data['address'],
                    city=data['city'],
                    postal_code=data['postal_code'],
                    is_primary=not SavedAddress.objects.filter(user=user).exists()  # First address is primary
                )
                message = 'Address saved successfully!'
                
            elif action == 'edit':
                # Update existing address
                address_id = data.get('id')
                try:
                    address = SavedAddress.objects.get(id=address_id, user=user)
                    address.name = data['name']
                    address.email = data['email']
                    address.phone = data['phone']
                    address.address = data['address']
                    address.city = data['city']
                    address.postal_code = data['postal_code']
                    address.save()
                    message = 'Address updated successfully!'
                except SavedAddress.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Address not found'})
            
            return JsonResponse({'success': True, 'message': message})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def save_payment_info(request):
    """
    Save or update user's payment method
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            action = data.get('action')
            
            # Get user from session
            username = request.session.get('username', 'default_user')
            user, created = User.objects.get_or_create(username=username)
            
            # Extract last 4 digits from card number
            card_number = data['card_number'].replace(' ', '')  # Remove spaces
            last_four = card_number[-4:] if len(card_number) >= 4 else card_number
            
            # Determine card type (simplified)
            if card_number.startswith('4'):
                card_type = 'visa'
            elif card_number.startswith('5'):
                card_type = 'mastercard'
            elif card_number.startswith('3'):
                card_type = 'amex'
            else:
                card_type = 'other'
            
            # Parse expiry input: support either combined 'expiry' (MM/YY) or separate fields
            expiry_month = data.get('expiry_month')
            expiry_year = data.get('expiry_year')
            if not expiry_month or not expiry_year:
                expiry_combined = data.get('expiry', '').strip()
                if '/' in expiry_combined:
                    mm, yy = [part.strip() for part in expiry_combined.split('/')[:2]]
                    expiry_month = mm.zfill(2)
                    expiry_year = yy if len(yy) == 4 else f"20{yy}"
            
            if action == 'add':
                # Create new payment method
                payment = SavedPaymentMethod.objects.create(
                    user=user,
                    cardholder_name=data['cardholder_name'],
                    card_type=card_type,
                    last_four=last_four,
                    expiry_month=expiry_month,
                    expiry_year=expiry_year,
                    is_primary=not SavedPaymentMethod.objects.filter(user=user).exists()  # First card is primary
                )
                message = 'Payment method saved successfully!'
                
            elif action == 'edit':
                # Update existing payment method
                payment_id = data.get('id')
                try:
                    payment = SavedPaymentMethod.objects.get(id=payment_id, user=user)
                    payment.cardholder_name = data['cardholder_name']
                    payment.last_four = last_four
                    payment.expiry_month = expiry_month
                    payment.expiry_year = expiry_year
                    payment.save()
                    message = 'Payment method updated successfully!'
                except SavedPaymentMethod.DoesNotExist:
                    return JsonResponse({'success': False, 'message': 'Payment method not found'})
            
            return JsonResponse({'success': True, 'message': message})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})


def get_saved_info(request):
    """
    Get user's saved addresses and payment methods
    """
    try:
        username = request.session.get('username', 'default_user')
        user, created = User.objects.get_or_create(username=username)
        
        addresses = SavedAddress.objects.filter(user=user)
        payment_methods = SavedPaymentMethod.objects.filter(user=user)
        
        data = {
            'addresses': list(addresses.values()),
            'payment_methods': list(payment_methods.values())
        }
        
        return JsonResponse({'success': True, 'data': data})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def get_address_details(request, address_id):
    """
    Get details of a specific saved address
    """
    try:
        username = request.session.get('username', 'default_user')
        user, created = User.objects.get_or_create(username=username)
        
        address = SavedAddress.objects.get(id=address_id, user=user)
        
        data = {
            'id': address.id,
            'name': address.name,
            'email': address.email,
            'phone': address.phone,
            'address': address.address,
            'city': address.city,
            'postal_code': address.postal_code
        }
        
        return JsonResponse({'success': True, 'address': data})
        
    except SavedAddress.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Address not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


def get_payment_details(request, payment_id):
    """
    Get details of a specific saved payment method (masked)
    """
    try:
        username = request.session.get('username', 'default_user')
        user, created = User.objects.get_or_create(username=username)
        
        pm = SavedPaymentMethod.objects.get(id=payment_id, user=user)
        
        data = {
            'id': pm.id,
            'cardholder_name': pm.cardholder_name,
            'card_type': pm.card_type,
            'last_four': pm.last_four,
            'expiry_month': pm.expiry_month,
            'expiry_year': pm.expiry_year,
        }
        
        return JsonResponse({'success': True, 'payment': data})
    except SavedPaymentMethod.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Payment method not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# Lightweight endpoint to set selected payment method in session
@csrf_exempt
@require_POST
def set_payment_method(request):
    method = request.POST.get('method', '').strip()
    if not method:
        return JsonResponse({'success': False, 'error': 'method required'}, status=400)
    # Normalize common labels
    normalized = method
    if method.lower() in ['cod', 'cash', 'cash on delivery']:
        normalized = 'Cash on Delivery'
    request.session['payment_method'] = normalized
    return JsonResponse({'success': True})

