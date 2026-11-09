from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User


class LoginTests(APITestCase):

    def setUp(self):
        self.url = "/api/auth/login/"

        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="Test@123456",
            is_active=True,
            is_verified=True
        )

        self.valid_data = {
            "email": "test@example.com",
            "password": "Test@123456"
        }

    # 1. Successful login
    def test_login_success(self):
        response = self.client.post(
            self.url,
            self.valid_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Login successful.")
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["email"], "test@example.com")

    # 2. Incorrect password
    def test_login_with_wrong_password(self):
        data = {
            "email": "test@example.com",
            "password": "WrongPassword123"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 3. Unregistered email
    def test_login_with_unknown_email(self):
        data = {
            "email": "unknown@example.com",
            "password": "Test@123456"
        }

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 4. Unverified account
    def test_login_with_unverified_account(self):
        self.user.is_verified = False
        self.user.save()

        response = self.client.post(
            self.url,
            self.valid_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("verify your email", str(response.data).lower())

    # 5. Inactive account
    def test_login_with_inactive_account(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            self.url,
            self.valid_data,
            format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 6. Missing password
    def test_login_without_password(self):
        data = {"email": "test@example.com"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # 7. Missing email
    def test_login_without_email(self):
        data = {"password": "Test@123456"}

        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)