def cart_context(request):
    """Добавляет информацию о корзине в контекст всех шаблонов"""
    cart = request.session.get('cart', {})
    cart_count = len(cart)

    return {
        'cart_count': cart_count,
    }