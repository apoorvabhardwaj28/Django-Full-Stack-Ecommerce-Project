from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile
import re


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            "placeholder": "Enter your email",
            "class": "form-input"
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            "placeholder": "Enter your phone number",
            "class": "form-input"
        })
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Create a password",
            "class": "form-input"
        })
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm your password",
            "class": "form-input"
        })
    )

    class Meta:
        model = User
        fields = ["email", "phone", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "").strip()

        if phone:
            if not re.fullmatch(r"^\d{10,15}$", phone):
                raise forms.ValidationError("Enter a valid phone number with 10 to 15 digits.")
        return phone

    def _generate_username(self, email):
        base_username = email.split("@")[0]
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        return username

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"]
        phone = self.cleaned_data.get("phone", "")

        user.email = email
        user.username = self._generate_username(email)

        if commit:
            user.save()
            UserProfile.objects.get_or_create(
                user=user,
                defaults={"phone": phone}
            )

        return user


class EmailLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email Address",
        widget=forms.EmailInput(attrs={
            "placeholder": "Enter your email",
            "class": "form-input"
        })
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter your password",
            "class": "form-input"
        })
    )