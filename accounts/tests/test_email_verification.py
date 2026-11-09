
from datetime import timedelta

from django.utils import timezone
from django.contrib.auth.hashers import make_password

from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, EmailOTP


class EmailVerificationTests(APITestCase):

    def setUp(self):
        self.url = "/api/auth/verify-email/"

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="Test@123456",
            is_active=False,
            is_verified=False
        )

        self.otp = "123456"

    def create_otp(
        self,
        otp=None,
        expires_at=None,
        is_used=False
    ):
        return EmailOTP.objects.create(
            user=self.user,
            otp_hash=make_password(otp or self.otp),
            purpose="email_verification",
            expires_at=expires_at or (
                timezone.now() + timedelta(minutes=5)
            ),
            is_used=is_used
        )

    def test_email_verification_success(self):
        self.create_otp()

        response = self.client.post(
            self.url,
            {
                "email": "test@example.com",
                "otp": self.otp
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertTrue(self.user.is_verified)
        self.assertTrue(self.user.is_active)

    def test_email_verification_with_wrong_otp(self):
        self.create_otp()

        response = self.client.post(
            self.url,
            {
                "email": "test@example.com",
                "otp": "999999"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.user.refresh_from_db()

        self.assertFalse(self.user.is_verified)

    def test_email_verification_with_expired_otp(self):
        self.create_otp(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        response = self.client.post(
            self.url,
            {
                "email": "test@example.com",
                "otp": self.otp
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.user.refresh_from_db()

        self.assertFalse(self.user.is_verified)

    def test_email_verification_with_used_otp(self):
        self.create_otp(is_used=True)

        response = self.client.post(
            self.url,
            {
                "email": "test@example.com",
                "otp": self.otp
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.user.refresh_from_db()

        self.assertFalse(self.user.is_verified)

    def test_email_verification_with_unknown_email(self):
        response = self.client.post(
            self.url,
            {
                "email": "unknown@example.com",
                "otp": self.otp
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )
