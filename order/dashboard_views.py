import csv
import json
from decimal import Decimal
from datetime import datetime, timedelta
import csv
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required


from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from .models import Order, OrderItem
from products.models import Product, Review, Wishlist


@staff_member_required
def admin_dashboard(request):

    # =========================
    # DATE FILTER
    # =========================

    filter_type = request.GET.get("range", "30")

    today = timezone.now().date()

    if filter_type == "7":
        start_date = today - timedelta(days=7)

    elif filter_type == "today":
        start_date = today

    elif filter_type == "custom":
        start = request.GET.get("start")
        end = request.GET.get("end")

        if start and end:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
            end_date = datetime.strptime(end, "%Y-%m-%d").date()

        else:
            start_date = today - timedelta(days=30)
            end_date = today

    else:
        start_date = today - timedelta(days=30)

    end_date = today


    # =========================
    # BASIC COUNTS
    # =========================

    total_orders = Order.objects.count()
    paid_orders = Order.objects.filter(paid=True).count()
    pending_orders = Order.objects.filter(status="pending").count()

    total_users = User.objects.count()
    total_products = Product.objects.count()
    total_reviews = Review.objects.count()
    total_wishlist_items = Wishlist.objects.count()


    # =========================
    # REVENUE
    # =========================

    total_revenue = (
        Order.objects.filter(paid=True)
        .aggregate(total=Sum("total_price"))["total"]
        or Decimal("0.00")
    )

    today_revenue = (
        Order.objects.filter(paid=True, created__date=today)
        .aggregate(total=Sum("total_price"))["total"]
        or Decimal("0.00")
    )

    week_revenue = (
        Order.objects.filter(paid=True, created__date__gte=today - timedelta(days=7))
        .aggregate(total=Sum("total_price"))["total"]
        or Decimal("0.00")
    )

    month_revenue = (
        Order.objects.filter(paid=True, created__month=today.month)
        .aggregate(total=Sum("total_price"))["total"]
        or Decimal("0.00")
    )


    # =========================
    # RECENT ORDERS
    # =========================

    recent_orders = Order.objects.select_related("user").order_by("-created")[:10]


    # =========================
    # TOP PRODUCTS
    # =========================

    line_total = ExpressionWrapper(
        F("price") * F("quantity"),
        output_field=DecimalField(max_digits=12, decimal_places=2),
    )

    top_products = (
        OrderItem.objects.values("product__name")
        .annotate(total_quantity=Sum("quantity"), total_revenue=Sum(line_total))
        .order_by("-total_quantity")[:6]
    )


    # =========================
    # TOP CUSTOMERS
    # =========================

    top_customers = (
        Order.objects.filter(paid=True)
        .values("user__username")
        .annotate(order_count=Count("id"), total_spent=Sum("total_price"))
        .order_by("-total_spent")[:6]
    )


    # =========================
    # LOW STOCK
    # =========================

    low_stock_products = Product.objects.filter(stock__lte=5)[:6]


    # =========================
    # REVENUE CHART
    # =========================

    revenue_queryset = (
        Order.objects.filter(paid=True, created__date__gte=start_date)
        .annotate(day=TruncDate("created"))
        .values("day")
        .annotate(total=Sum("total_price"))
        .order_by("day")
    )

    revenue_labels = [x["day"].strftime("%d %b") for x in revenue_queryset]
    revenue_values = [float(x["total"]) for x in revenue_queryset]


    # =========================
    # ORDERS CHART
    # =========================

    orders_queryset = (
        Order.objects.filter(created__date__gte=start_date)
        .annotate(day=TruncDate("created"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )

    orders_labels = [x["day"].strftime("%d %b") for x in orders_queryset]
    orders_values = [x["count"] for x in orders_queryset]


    # =========================
    # STATUS CHART
    # =========================

    status_queryset = (
        Order.objects.values("status")
        .annotate(count=Count("id"))
        .order_by("status")
    )

    status_labels = [x["status"].title() for x in status_queryset]
    status_values = [x["count"] for x in status_queryset]


    context = {

        "total_orders": total_orders,
        "paid_orders": paid_orders,
        "pending_orders": pending_orders,

        "total_users": total_users,
        "total_products": total_products,
        "total_reviews": total_reviews,
        "total_wishlist_items": total_wishlist_items,

        "total_revenue": total_revenue,
        "today_revenue": today_revenue,
        "week_revenue": week_revenue,
        "month_revenue": month_revenue,

        "recent_orders": recent_orders,
        "top_products": top_products,
        "top_customers": top_customers,
        "low_stock_products": low_stock_products,

        "revenue_labels_json": json.dumps(revenue_labels),
        "revenue_values_json": json.dumps(revenue_values),

        "orders_labels_json": json.dumps(orders_labels),
        "orders_values_json": json.dumps(orders_values),

        "status_labels_json": json.dumps(status_labels),
        "status_values_json": json.dumps(status_values),

        "range": filter_type,
    }

    return render(request, "order/admin_dashboard.html", context)



# =========================
# EXPORT CSV
# =========================

@staff_member_required
def export_orders_csv(request):

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="orders.csv"'

    writer = csv.writer(response)

    writer.writerow(["Order ID", "User", "Amount", "Status", "Date"])

    orders = Order.objects.all()

@staff_member_required
def export_csv(request):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="orders_report.csv"'

    writer = csv.writer(response)
    writer.writerow(["Order ID", "Customer", "Amount", "Status", "Created"])

    orders = Order.objects.select_related("user").all()

    for order in orders:
        writer.writerow([
            order.pk,
            order.user.username if order.user else "Guest",
            order.total_price,
            order.status,
            order.created.strftime("%Y-%m-%d %H:%M"),
        ])

    return response