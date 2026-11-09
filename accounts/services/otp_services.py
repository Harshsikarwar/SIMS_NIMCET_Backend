
import secrets
from datetime import timedelta

from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts.models import EmailOTP
from accounts.services.email_services import send_otp_email


OTP_EXPIRY_MINUTES = 5
OTP_RESEND_COOLDOWN = 60
MAX_OTP_ATTEMPTS = 5


def generate_otp():
    """Generate a secure 6-digit OTP."""
    return str(secrets.randbelow(900000) + 100000)


def create_and_send_otp(user, purpose, target_email=None):
    """Generate, store and email an OTP."""

    email = target_email or user.email

    latest_otp = EmailOTP.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False
    ).order_by("-created_at").first()

    if latest_otp:
        elapsed = (timezone.now() - latest_otp.created_at).total_seconds()

        if elapsed < OTP_RESEND_COOLDOWN:
            raise ValidationError(
                "Please wait before requesting another OTP."
            )

        latest_otp.is_used = True
        latest_otp.save(update_fields=["is_used"])

    otp = generate_otp()

    otp_record = EmailOTP.objects.create(
        user=user,
        otp_hash=make_password(otp),
        purpose=purpose,
        expires_at=timezone.now() + timedelta(
            minutes=OTP_EXPIRY_MINUTES
        ),
        target_email=target_email,
    )

    try:
        send_otp_email(email, otp, purpose)
    except Exception:
        otp_record.delete()
        raise ValidationError(
            "Unable to send OTP. Please try again later."
        )

    return True


def verify_otp(user, otp, purpose):
    """Verify OTP and return its database record."""

    otp_record = EmailOTP.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False
    ).order_by("-created_at").first()

    if not otp_record:
        raise ValidationError("OTP not found or already used.")

    if otp_record.expires_at <= timezone.now():
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])
        raise ValidationError("OTP has expired.")

    if otp_record.attempts >= MAX_OTP_ATTEMPTS:
        otp_record.is_used = True
        otp_record.save(update_fields=["is_used"])
        raise ValidationError("Maximum OTP attempts exceeded.")

    if not check_password(otp, otp_record.otp_hash):
        otp_record.attempts += 1

        if otp_record.attempts >= MAX_OTP_ATTEMPTS:
            otp_record.is_used = True

        otp_record.save(update_fields=["attempts", "is_used"])

        raise ValidationError("Invalid OTP.")

    otp_record.is_used = True
    otp_record.save(update_fields=["is_used"])

    return otp_record
