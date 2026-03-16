from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from products.models import Product
from order.models import Coupon


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)

    if product.stock <= 0:
        messages.error(request, f"{product.name} is out of stock.")
        return redirect("product_list")

    cart = request.session.get('cart', {})
    product_id = str(product_id)

    current_quantity = cart.get(product_id, {}).get("quantity", 0)

    if current_quantity >= product.stock:
        messages.error(request, f"Only {product.stock} item(s) of {product.name} available in stock.")
        return redirect('cart_detail')

    if product_id in cart:
        cart[product_id]['quantity'] += 1
    else:
        cart[product_id] = {
            'name': product.name,
            'price': float(product.price),
            'quantity': 1,
        }

    request.session['cart'] = cart
    messages.success(request, f"{product.name} added to cart.")
    return redirect('cart_detail')


@login_required
def cart_detail(request):
    cart = request.session.get('cart', {})
    total_price = Decimal("0.00")
    has_stock_issue = False

    for product_id, item in list(cart.items()):
        item['subtotal'] = Decimal(str(item['price'])) * item['quantity']
        item['stock_issue'] = False
        item['stock_message'] = ""

        try:
            product = Product.objects.get(id=product_id)
            item['current_stock'] = product.stock
            item['available'] = product.available

            if not product.available or product.stock <= 0:
                item['stock_issue'] = True
                item['stock_message'] = "Out of stock"
                has_stock_issue = True
            elif item['quantity'] > product.stock:
                item['stock_issue'] = True
                item['stock_message'] = f"Only {product.stock} left in stock"
                has_stock_issue = True
        except Product.DoesNotExist:
            item['stock_issue'] = True
            item['stock_message'] = "Product no longer available"
            has_stock_issue = True

        total_price += item['subtotal']

    coupon_code = request.session.get("coupon_code")
    discount_amount = Decimal(str(request.session.get("discount_amount", "0.00")))
    final_total = total_price - discount_amount

    if final_total < Decimal("0.00"):
        final_total = Decimal("0.00")

    return render(request, 'cart/cart_detail.html', {
        'cart': cart,
        'total_price': total_price,
        'coupon_code': coupon_code,
        'discount_amount': discount_amount,
        'final_total': final_total,
        'has_stock_issue': has_stock_issue,
    })


@login_required
def apply_coupon(request):
    if request.method == "POST":
        code = request.POST.get("coupon_code", "").strip().upper()
        cart = request.session.get('cart', {})

        if not cart:
            messages.error(request, "Your cart is empty.")
            return redirect('cart_detail')

        total_price = Decimal("0.00")
        for item in cart.values():
            total_price += Decimal(str(item['price'])) * item['quantity']

        try:
            coupon = Coupon.objects.get(code__iexact=code, active=True)
        except Coupon.DoesNotExist:
            messages.error(request, "Invalid or inactive coupon code.")
            request.session.pop("coupon_code", None)
            request.session.pop("discount_amount", None)
            return redirect('cart_detail')

        if coupon.discount_type == "percent":
            discount_amount = (total_price * coupon.discount_value) / Decimal("100")
        else:
            discount_amount = coupon.discount_value

        if discount_amount > total_price:
            discount_amount = total_price

        request.session["coupon_code"] = coupon.code
        request.session["discount_amount"] = str(discount_amount)

        messages.success(request, f"Coupon '{coupon.code}' applied successfully.")
        return redirect('cart_detail')

    return redirect('cart_detail')


@login_required
def remove_coupon(request):
    request.session.pop("coupon_code", None)
    request.session.pop("discount_amount", None)
    messages.success(request, "Coupon removed successfully.")
    return redirect('cart_detail')


@login_required
def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)

    if product_id in cart:
        del cart[product_id]

    request.session['cart'] = cart
    return redirect('cart_detail')


@login_required
def increase_quantity(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)

    if product_id in cart:
        try:
            product = Product.objects.get(id=product_id, available=True)
            if cart[product_id]['quantity'] >= product.stock:
                messages.error(request, f"Only {product.stock} item(s) available for {product.name}.")
                return redirect('cart_detail')
            cart[product_id]['quantity'] += 1
        except Product.DoesNotExist:
            messages.error(request, "Product is no longer available.")

    request.session['cart'] = cart
    return redirect('cart_detail')


@login_required
def decrease_quantity(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)

    if product_id in cart:
        cart[product_id]['quantity'] -= 1

        if cart[product_id]['quantity'] <= 0:
            del cart[product_id]

    request.session['cart'] = cart
    return redirect('cart_detail')