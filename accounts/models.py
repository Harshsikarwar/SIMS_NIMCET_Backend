from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Create your models here.
class User(AbstractUser):
    email = models.EmailField(unique=True)
    is_verified = models.BooleanField(default=False)

class EmailOTP(models.Model):

    class Purpose(models.TextChoices):
        EMAIL_VERIFICATION = "email_verification", "Email Verification"
        PASSWORD_RESET = "password_reset", "Password Reset"
        EMAIL_UPDATE = "email_update", "Email Update"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="email_otps"
    )

    otp_hash = models.CharField(max_length=255)

    purpose = models.CharField(
        max_length=30,
        choices=Purpose.choices
    )

    target_email = models.EmailField(
        null=True,
        blank=True
    )

    expires_at = models.DateTimeField()

    attempts = models.PositiveSmallIntegerField(default=0)

    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.email} - {self.purpose}"