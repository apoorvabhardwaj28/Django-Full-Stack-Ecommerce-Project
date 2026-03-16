from django.contrib import admin
from .models import UserProfile, Address
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone", "is_email_verified", "created_at")
    search_fields = ("user__username", "user__email", "phone")
    list_filter = ("is_email_verified", "created_at")
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "user",
        "city",
        "state",
        "postal_code",
        "is_default",
        "created_at",
    )

    search_fields = (
        "full_name",
        "user__username",
        "user__email",
        "city",
        "postal_code",
    )

    list_filter = ("city", "state", "country", "is_default")

    ordering = ("-created_at",)