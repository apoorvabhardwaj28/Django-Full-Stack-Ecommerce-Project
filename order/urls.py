from django.urls import path
from .views import checkout, payment_success, order_success, order_history, download_invoice, cancel_order
from .dashboard_views import admin_dashboard, export_csv

urlpatterns = [
    path('checkout/', checkout, name='checkout'),
    path('payment-success/', payment_success, name='payment_success'),
    path('success/', order_success, name='order_success'),
    path('history/', order_history, name='order_history'),
    path('invoice/<int:order_id>/', download_invoice, name='download_invoice'),
    path('cancel/<int:order_id>/', cancel_order, name='cancel_order'),

    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('dashboard/export/csv/', export_csv, name='export_csv'),
]