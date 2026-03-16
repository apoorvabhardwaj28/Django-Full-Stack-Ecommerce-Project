from decimal import Decimal, InvalidOperation
from io import BytesIO

import razorpay
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from accounts.models import Address
from products.models import Product
from .models import Order, OrderItem


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal("0.00")


@login_required
def checkout(request):
    cart = request.session.get("cart", {})

    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect("cart_detail")

    addresses = Address.objects.filter(user=request.user).order_by("-is_default", "-created_at")
    default_address = addresses.filter(is_default=True).first()

    cart_items = []
    subtotal_amount = Decimal("0.00")
    has_stock_issue = False

    for product_pk, item in cart.items():
        price = _to_decimal(item.get("price", 0))
        quantity = int(item.get("quantity", 0))
        item_total = price * quantity

        stock_message = ""
        try:
            product = Product.objects.get(pk=product_pk)
            if not product.available or product.stock <= 0:
                stock_message = "Out of stock"
                has_stock_issue = True
            elif quantity > product.stock:
                stock_message = f"Only {product.stock} left in stock"
                has_stock_issue = True
        except Product.DoesNotExist:
            stock_message = "Product no longer available"
            has_stock_issue = True

        cart_items.append(
            {
                "product_id": product_pk,
                "name": item.get("name", "Product"),
                "price": price,
                "quantity": quantity,
                "item_total": item_total,
                "stock_message": stock_message,
            }
        )
        subtotal_amount += item_total

    coupon_code = request.session.get("coupon_code", "")
    discount_amount = _to_decimal(request.session.get("discount_amount", "0.00"))
    total_amount = subtotal_amount - discount_amount

    if total_amount < Decimal("0.00"):
        total_amount = Decimal("0.00")

    total_amount_paise = int(total_amount * 100)

    if request.method == "POST":
        if has_stock_issue:
            messages.error(request, "Some items in your cart are out of stock or exceed available stock.")
            return redirect("cart_detail")

        address_pk = request.POST.get("address_id")

        if not address_pk:
            messages.error(request, "Please select a delivery address.")
            return render(
                request,
                "order/checkout.html",
                {
                    "cart_items": cart_items,
                    "subtotal_amount": subtotal_amount,
                    "discount_amount": discount_amount,
                    "coupon_code": coupon_code,
                    "total_amount": total_amount,
                    "addresses": addresses,
                    "default_address": default_address,
                    "has_stock_issue": has_stock_issue,
                },
            )

        selected_address = get_object_or_404(Address, pk=address_pk, user=request.user)

        order = Order.objects.create(
            user=request.user,
            address=selected_address,
            full_name=selected_address.full_name,
            phone=selected_address.phone,
            address_line_1=selected_address.address_line_1,
            address_line_2=selected_address.address_line_2 or "",
            city=selected_address.city,
            state=selected_address.state,
            postal_code=selected_address.postal_code,
            country=selected_address.country,
            paid=False,
            status="pending",
            coupon_code=coupon_code or "",
            discount_amount=discount_amount,
            total_price=total_amount,
        )

        for product_pk, item in cart.items():
            product = get_object_or_404(Product, pk=product_pk)

            OrderItem.objects.create(
                order=order,
                product=product,
                price=_to_decimal(item.get("price", 0)),
                quantity=int(item.get("quantity", 1)),
            )

        order.calculate_total()

        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

        payment = client.order.create({
            "amount": total_amount_paise,
            "currency": "INR",
            "payment_capture": 1,
        })

        request.session["order_id"] = order.pk

        context = {
            "payment": payment,
            "razorpay_key_id": settings.RAZORPAY_KEY_ID,
            "total_amount": total_amount,
            "order": order,
        }

        return render(request, "order/payment.html", context)

    context = {
        "cart_items": cart_items,
        "subtotal_amount": subtotal_amount,
        "discount_amount": discount_amount,
        "coupon_code": coupon_code,
        "total_amount": total_amount,
        "addresses": addresses,
        "default_address": default_address,
        "has_stock_issue": has_stock_issue,
    }
    return render(request, "order/checkout.html", context)


@login_required
def payment_success(request):
    order_pk = request.session.get("order_id")

    if not order_pk:
        return redirect("order_success")

    order = get_object_or_404(Order, pk=order_pk, user=request.user)

    if order.paid and order.stock_deducted:
        request.session["last_order_id"] = order.pk
        request.session.pop("order_id", None)
        return redirect("order_success")

    with transaction.atomic():
        order_items = order.items.select_related("product")

        for item in order_items:
            product = item.product

            if not product.available or product.stock < item.quantity:
                messages.error(request, f"Payment completed, but {product.name} does not have enough stock now. Please contact support/admin.")
                return redirect("order_history")

        for item in order_items:
            product = item.product
            product.stock -= item.quantity

            if product.stock <= 0:
                product.stock = 0
                product.available = False

            product.save(update_fields=["stock", "available"])

        order.paid = True
        order.status = "processing"
        order.stock_deducted = True
        order.save(update_fields=["paid", "status", "stock_deducted"])

    if request.user.email:
        full_address = (
            f"{order.address_line_1}, "
            f"{order.address_line_2 + ', ' if order.address_line_2 else ''}"
            f"{order.city}, {order.state} - {order.postal_code}, {order.country}"
        )

        send_mail(
            subject="Order Confirmation - MyStore",
            message=(
                f"Hello {request.user.email},\n\n"
                f"Your payment was successful.\n"
                f"Your order ID is #{order.pk}.\n\n"
                f"Shipping Details:\n"
                f"Name: {order.full_name}\n"
                f"Phone: {order.phone}\n"
                f"Address: {full_address}\n\n"
                f"Order Total: ₹{order.total_price}\n"
                f"Status: {order.status.title()}\n\n"
                f"Thank you for shopping with MyStore."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[request.user.email],
            fail_silently=False,
        )

    request.session["cart"] = {}
    request.session["last_order_id"] = order.pk
    request.session.pop("order_id", None)
    request.session.pop("coupon_code", None)
    request.session.pop("discount_amount", None)

    return redirect("order_success")


@login_required
def order_success(request):
    last_order_pk = request.session.get("last_order_id")
    order = None

    if last_order_pk:
        order = Order.objects.filter(pk=last_order_pk, user=request.user).first()

    return render(request, "order/order_success.html", {"order": order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items__product").order_by("-created")
    return render(request, "order/order_history.html", {"orders": orders})


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    if order.status not in ["pending", "processing"]:
        messages.error(request, "This order cannot be cancelled.")
        return redirect("order_history")

    if order.status == "cancelled":
        messages.info(request, "This order is already cancelled.")
        return redirect("order_history")

    with transaction.atomic():
        if order.stock_deducted:
            for item in order.items.select_related("product"):
                product = item.product
                product.stock += item.quantity
                if product.stock > 0:
                    product.available = True
                product.save(update_fields=["stock", "available"])

        order.status = "cancelled"
        order.save(update_fields=["status"])

    messages.success(request, f"Order #{order.pk} cancelled successfully.")
    return redirect("order_history")


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, pk=order_id, user=request.user)

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "MyStore - Invoice")

    y -= 30
    pdf.setFont("Helvetica", 11)
    pdf.drawString(50, y, f"Order ID: #{order.pk}")

    y -= 20
    pdf.drawString(50, y, f"Date: {order.created.strftime('%d-%m-%Y %I:%M %p')}")

    y -= 20
    pdf.drawString(50, y, f"Customer: {order.full_name}")

    y -= 20
    pdf.drawString(50, y, f"Phone: {order.phone}")

    y -= 20
    pdf.drawString(
        50,
        y,
        f"Address: {order.address_line_1}, {order.city}, {order.state} - {order.postal_code}, {order.country}"
    )

    y -= 35
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Items")

    y -= 20
    pdf.setFont("Helvetica", 11)

    for item in order.items.all():
        line = f"{item.product.name} | Qty: {item.quantity} | Price: ₹{item.price} | Total: ₹{item.get_total_price()}"
        pdf.drawString(50, y, line)
        y -= 20

        if y < 80:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 11)

    y -= 10
    pdf.setFont("Helvetica-Bold", 12)

    if order.coupon_code:
        pdf.drawString(50, y, f"Coupon Applied: {order.coupon_code}")
        y -= 20
        pdf.drawString(50, y, f"Discount: ₹{order.discount_amount}")
        y -= 20

    pdf.drawString(50, y, f"Final Total: ₹{order.total_price}")

    y -= 20
    pdf.drawString(50, y, f"Payment Status: {'Paid' if order.paid else 'Pending'}")

    y -= 20
    pdf.drawString(50, y, f"Order Status: {order.status.title()}")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="invoice_order_{order.pk}.pdf"'
    return response