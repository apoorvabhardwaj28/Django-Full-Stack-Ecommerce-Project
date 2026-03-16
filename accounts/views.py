from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .forms import SignupForm, EmailLoginForm
from .models import UserProfile, Address


def signup(request):
    if request.user.is_authenticated:
        return redirect("product_list")

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.phone = form.cleaned_data.get("phone", "")
            profile.is_email_verified = False
            profile.generate_otp()
            profile.save()

            send_mail(
                subject="Verify your email - OTP",
                message=(
                    f"Hello {user.email},\n\n"
                    f"Your OTP for email verification is: {profile.email_otp}\n\n"
                    f"Thank you."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            request.session["verify_user_id"] = user.id
            messages.success(request, "Account created. OTP has been sent to your email.")
            return redirect("verify_email")
    else:
        form = SignupForm()

    return render(request, "accounts/signup.html", {"form": form})


def verify_email(request):
    user_id = request.session.get("verify_user_id")

    if not user_id:
        messages.error(request, "Session expired. Please sign up again.")
        return redirect("signup")

    try:
        user = User.objects.get(id=user_id)
        profile = UserProfile.objects.get(user=user)
    except (User.DoesNotExist, UserProfile.DoesNotExist):
        messages.error(request, "User not found.")
        return redirect("signup")

    if request.method == "POST":
        entered_otp = request.POST.get("otp", "").strip()

        if entered_otp == profile.email_otp:
            profile.is_email_verified = True
            profile.email_otp = ""
            profile.save(update_fields=["is_email_verified", "email_otp"])

            user.is_active = True
            user.save(update_fields=["is_active"])

            login(request, user, backend="accounts.backends.EmailBackend")
            request.session.pop("verify_user_id", None)

            messages.success(request, "Email verified successfully. You are now logged in.")
            return redirect("product_list")
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, "accounts/verify_email.html")


class CustomLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailLoginForm
    redirect_authenticated_user = True

    def get_success_url(self):
        return "/store/"


class CustomLogoutView(LogoutView):
    next_page = "landing_page"


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    addresses = Address.objects.filter(user=request.user).order_by("-is_default", "-created_at")

    context = {
        "profile": profile,
        "addresses": addresses,
    }
    return render(request, "accounts/profile.html", context)


@login_required
def add_address(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()
        address_line_1 = request.POST.get("address_line_1", "").strip()
        address_line_2 = request.POST.get("address_line_2", "").strip()
        city = request.POST.get("city", "").strip()
        state = request.POST.get("state", "").strip()
        postal_code = request.POST.get("postal_code", "").strip()
        country = request.POST.get("country", "India").strip()
        is_default = request.POST.get("is_default") == "on"

        if not full_name or not phone or not address_line_1 or not city or not state or not postal_code:
            messages.error(request, "Please fill all required address fields.")
            return redirect("profile")

        if is_default:
            Address.objects.filter(user=request.user, is_default=True).update(is_default=False)

        Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            address_line_1=address_line_1,
            address_line_2=address_line_2,
            city=city,
            state=state,
            postal_code=postal_code,
            country=country,
            is_default=is_default,
        )

        messages.success(request, "Address added successfully.")
        return redirect("profile")

    return redirect("profile")


@login_required
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        address.full_name = request.POST.get("full_name", "").strip()
        address.phone = request.POST.get("phone", "").strip()
        address.address_line_1 = request.POST.get("address_line_1", "").strip()
        address.address_line_2 = request.POST.get("address_line_2", "").strip()
        address.city = request.POST.get("city", "").strip()
        address.state = request.POST.get("state", "").strip()
        address.postal_code = request.POST.get("postal_code", "").strip()
        address.country = request.POST.get("country", "India").strip()
        is_default = request.POST.get("is_default") == "on"

        if not address.full_name or not address.phone or not address.address_line_1 or not address.city or not address.state or not address.postal_code:
            messages.error(request, "Please fill all required address fields.")
            return redirect("profile")

        if is_default:
            Address.objects.filter(user=request.user, is_default=True).exclude(pk=address.pk).update(is_default=False)
        address.is_default = is_default
        address.save()

        messages.success(request, "Address updated successfully.")
        return redirect("profile")

    return render(request, "accounts/edit_address.html", {"address": address})


@login_required
def delete_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == "POST":
        address.delete()
        messages.success(request, "Address deleted successfully.")
        return redirect("profile")

    return render(request, "accounts/delete_address.html", {"address": address})


@login_required
def set_default_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)

    Address.objects.filter(user=request.user, is_default=True).update(is_default=False)
    address.is_default = True
    address.save(update_fields=["is_default"])

    messages.success(request, "Default address updated successfully.")
    return redirect("profile")