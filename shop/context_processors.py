def cart_quantity(request):
    """Add cart quantity to all template contexts"""
    cart = request.session.get('cart', {})
    cart_quantity = sum(cart.values()) if cart else 0
    return {'cart_quantity': cart_quantity}
