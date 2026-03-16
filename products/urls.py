from django.urls import path
from .views import (
    product_list,
    product_detail,
    add_to_wishlist,
    remove_from_wishlist,
    wishlist_view,
    add_review,
    delete_review
)

urlpatterns = [

    path('', product_list, name='product_list'),

    path(
        'category/<slug:category_slug>/',
        product_list,
        name='products_by_category'
    ),

    path(
        'product/<slug:slug>/',
        product_detail,
        name='product_detail'
    ),

    # Wishlist URLs
    path(
        'wishlist/',
        wishlist_view,
        name='wishlist'
    ),

    path(
        'wishlist/add/<int:product_id>/',
        add_to_wishlist,
        name='add_to_wishlist'
    ),

    path(
        'wishlist/remove/<int:product_id>/',
        remove_from_wishlist,
        name='remove_from_wishlist'
    ),

    # Review URLs
    path(
        'review/add/<int:product_id>/',
        add_review,
        name='add_review'
    ),

    path(
        'review/delete/<int:product_id>/',
        delete_review,
        name='delete_review'
    ),
]