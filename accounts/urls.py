from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from .views import (
    signup,
    verify_email,
    CustomLoginView,
    CustomLogoutView,
    profile_view,
    add_address,
    edit_address,
    delete_address,
    set_default_address,
)

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('verify-email/', verify_email, name='verify_email'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),

    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='accounts/password_reset.html',
            email_template_name='accounts/password_reset_email.html',
            subject_template_name='accounts/password_reset_subject.txt',
            success_url=reverse_lazy('password_reset_done'),
        ),
        name='password_reset'
    ),
    path(
        'password-reset/done/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='accounts/password_reset_done.html'
        ),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='accounts/password_reset_confirm.html',
            success_url=reverse_lazy('password_reset_complete'),
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='accounts/password_reset_complete.html'
        ),
        name='password_reset_complete'
    ),

    path('profile/', profile_view, name='profile'),
    path('address/add/', add_address, name='add_address'),
    path('address/edit/<int:address_id>/', edit_address, name='edit_address'),
    path('address/delete/<int:address_id>/', delete_address, name='delete_address'),
    path('address/default/<int:address_id>/', set_default_address, name='set_default_address'),
]