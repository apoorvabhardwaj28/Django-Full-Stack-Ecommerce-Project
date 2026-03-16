from django.urls import path
from .views import (
    add_to_cart,
    cart_detail,
    remove_from_cart,
    increase_quantity,
    decrease_quantity,
    apply_coupon,
    remove_coupon,
)

urlpatterns = [
    path('', cart_detail, name='cart_detail'),
    path('add/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('remove/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
    path('increase/<int:product_id>/', increase_quantity, name='increase_quantity'),
    path('decrease/<int:product_id>/', decrease_quantity, name='decrease_quantity'),
    path('apply-coupon/', apply_coupon, name='apply_coupon'),
    path('remove-coupon/', remove_coupon, name='remove_coupon'),
]