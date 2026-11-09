
from unittest.mock import patch

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


class RegistrationTests(APITestCase):

    def setUp(self):
        self.url = "/api/auth/register/"

        self.valid_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test@123456",
            "confirm_password": "Test@123456",
        }

    @patch("accounts.views.send_verification_otp")
    def test_user_registration_success(self, mock_send_otp):
        response = self.client.post(
            self.url,
            self.valid_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            User.objects.filter(email="test@example.com").exists()
        )

        user = User.objects.get(email="test@example.com")

        self.assertFalse(user.is_verified)
        self.assertFalse(user.is_active)

        mock_send_otp.assert_called_once_with(user)

    def test_registration_with_duplicate_email(self):
        User.objects.create_user(
            username="existing",
            email="test@example.com",
            password="Test@123456"
        )

        response = self.client.post(
            self.url,
            self.valid_data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

    def test_registration_with_password_mismatch(self):
        data = self.valid_data.copy()
        data["confirm_password"] = "Different@123"

        response = self.client.post(
            self.url,
            data,
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST
        )

        self.assertFalse(
            User.objects.filter(email="test@example.com").exists()
        )
