
from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(email, otp, purpose="email_verification"):
    subjects = {
        "email_verification": "Verify Your SIMS-NIMCET Account",
        "password_reset": "SIMS-NIMCET Password Reset",
        "email_update": "Verify Your New Email Address",
    }

    subject = subjects.get(purpose, "SIMS-NIMCET Verification")

    message = f"""
Hello,

Your OTP for SIMS-NIMCET is: {otp}

This OTP is valid for 5 minutes.

If you did not request this, please ignore this email.

Regards,
SIMS-NIMCET Team
"""

    return send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
