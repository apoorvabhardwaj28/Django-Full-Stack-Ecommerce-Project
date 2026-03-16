from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Product, Category, Wishlist, Review


@login_required
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    query = request.GET.get('q')
    if query:
        products = products.filter(name__icontains=query)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)

    paginator = Paginator(products, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    wishlist_product_ids = Wishlist.objects.filter(
        user=request.user
    ).values_list('product_id', flat=True)

    context = {
        'category': category,
        'categories': categories,
        'page_obj': page_obj,
        'query': query,
        'wishlist_product_ids': wishlist_product_ids,
    }

    return render(request, 'products/product_list.html', context)


@login_required
def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    reviews = Review.objects.filter(product=product).select_related('user').order_by('-created_at')

    in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
    user_review = Review.objects.filter(user=request.user, product=product).first()

    recommended_products = Product.objects.filter(
        category=product.category,
        available=True
    ).exclude(id=product.id)[:4]

    recently_viewed = request.session.get("recently_viewed", [])

    if product.id in recently_viewed:
        recently_viewed.remove(product.id)

    recently_viewed.insert(0, product.id)
    recently_viewed = recently_viewed[:6]
    request.session["recently_viewed"] = recently_viewed

    recently_viewed_products = Product.objects.filter(
        id__in=recently_viewed,
        available=True
    ).exclude(id=product.id)

    recently_viewed_products = sorted(
        recently_viewed_products,
        key=lambda x: recently_viewed.index(x.id)
    )

    context = {
        'product': product,
        'in_wishlist': in_wishlist,
        'reviews': reviews,
        'user_review': user_review,
        'recommended_products': recommended_products,
        'recently_viewed_products': recently_viewed_products,
    }

    return render(request, 'products/product_detail.html', context)


@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)

    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    if created:
        messages.success(request, "Product added to wishlist.")
    else:
        messages.info(request, "Product is already in your wishlist.")

    return redirect(request.META.get('HTTP_REFERER', 'product_list'))


@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    wishlist_item = Wishlist.objects.filter(user=request.user, product=product)

    if wishlist_item.exists():
        wishlist_item.delete()
        messages.success(request, "Product removed from wishlist.")
    else:
        messages.info(request, "Product was not in your wishlist.")

    return redirect(request.META.get('HTTP_REFERER', 'wishlist'))


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product').order_by('-added_at')

    context = {
        'wishlist_items': wishlist_items,
    }

    return render(request, 'products/wishlist.html', context)


@login_required
def add_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)

    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if not rating or not comment:
            messages.error(request, "Please provide both rating and review comment.")
            return redirect('product_detail', slug=product.slug)

        existing_review = Review.objects.filter(user=request.user, product=product).first()

        if existing_review:
            messages.info(request, "You have already reviewed this product.")
            return redirect('product_detail', slug=product.slug)

        Review.objects.create(
            user=request.user,
            product=product,
            rating=int(rating),
            comment=comment
        )

        messages.success(request, "Your review has been added successfully.")
        return redirect('product_detail', slug=product.slug)

    return redirect('product_detail', slug=product.slug)


@login_required
def delete_review(request, product_id):
    product = get_object_or_404(Product, id=product_id, available=True)
    review = Review.objects.filter(user=request.user, product=product).first()

    if review:
        review.delete()
        messages.success(request, "Your review has been deleted.")
    else:
        messages.info(request, "Review not found.")

    return redirect('product_detail', slug=product.slug)