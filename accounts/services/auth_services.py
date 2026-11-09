
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework.exceptions import ValidationError

from accounts.services.otp_services import (
    create_and_send_otp,
    verify_otp,
)

User = get_user_model()


def send_verification_otp(user):
    """Send OTP for new user registration."""

    if user.is_verified:
        raise ValidationError("Email is already verified.")

    return create_and_send_otp(
        user=user,
        purpose="email_verification"
    )


@transaction.atomic
def verify_email(user, otp):
    """Verify email and activate the account."""

    if user.is_verified:
        raise ValidationError("Email is already verified.")

    verify_otp(
        user=user,
        otp=otp,
        purpose="email_verification"
    )

    user.is_verified = True
    user.is_active = True
    user.save(update_fields=["is_verified", "is_active"])

    return user


def resend_verification_otp(user):
    """Resend email verification OTP."""

    if user.is_verified:
        raise ValidationError("Email is already verified.")

    return create_and_send_otp(
        user=user,
        purpose="email_verification"
    )


def send_password_reset_otp(user):
    """Send OTP for password reset."""

    return create_and_send_otp(
        user=user,
        purpose="password_reset"
    )


@transaction.atomic
def reset_password(user, otp, new_password):
    """Verify OTP and reset password."""

    verify_otp(
        user=user,
        otp=otp,
        purpose="password_reset"
    )

    user.set_password(new_password)
    user.save(update_fields=["password"])

    return True


def send_email_update_otp(user, new_email):
    """Send OTP to the new email address."""

    if User.objects.filter(email__iexact=new_email).exists():
        raise ValidationError("Email is already registered.")

    return create_and_send_otp(
        user=user,
        purpose="email_update",
        target_email=new_email
    )


@transaction.atomic
def verify_email_update(user, otp):
    """Verify new email and update user email."""

    otp_record = verify_otp(
        user=user,
        otp=otp,
        purpose="email_update"
    )

    new_email = otp_record.target_email

    if not new_email:
        raise ValidationError("New email address not found.")

    if User.objects.filter(email__iexact=new_email).exclude(
        pk=user.pk
    ).exists():
        raise ValidationError("Email is already registered.")

    user.email = new_email
    user.is_verified = True
    user.save(update_fields=["email", "is_verified"])

    return user
