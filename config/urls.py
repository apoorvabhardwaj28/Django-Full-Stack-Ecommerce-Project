from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from order.dashboard_views import admin_dashboard
from config.views import landing_page

urlpatterns = [
    path('admin/', admin.site.urls),

    # Public landing page (first page of website)
    path('', landing_page, name='landing_page'),

    # Custom analytics dashboard
    path('dashboard/', admin_dashboard, name='admin_dashboard'),

    # Store apps
    path('store/', include('products.urls')),
    path('cart/', include('cart.urls')),
    path('order/', include('order.urls')),

    # Local account pages
    path('accounts/', include('accounts.urls')),

    # django-allauth
    path('accounts/', include('allauth.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)