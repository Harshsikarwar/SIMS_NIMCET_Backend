
from django.urls import path

from accounts.views import (
    RegisterView,
    VerifyEmailView,
    ResendOTPView,
    LoginView,
    LogoutView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    EmailUpdateRequestView,
    EmailUpdateVerifyView,
)

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("verify-email/", VerifyEmailView.as_view()),
    path("resend-otp/", ResendOTPView.as_view()),

    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),

    path("password-reset/", PasswordResetRequestView.as_view()),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view()),

    path("email-update/", EmailUpdateRequestView.as_view()),
    path("email-update/verify/", EmailUpdateVerifyView.as_view()),
]
