
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from accounts.models import User, EmailOTP
from accounts.services.otp_services import (
    generate_otp,
    create_and_send_otp,
    verify_otp,
)


class OTPServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="otpuser",
            email="otp@example.com",
            password="Test@123456",
            is_active=False,
            is_verified=False
        )

        self.purpose = "email_verification"
        self.otp = "123456"

    def create_otp(
        self,
        otp="123456",
        expires_at=None,
        attempts=0,
        is_used=False
    ):
        return EmailOTP.objects.create(
            user=self.user,
            otp_hash=make_password(otp),
            purpose=self.purpose,
            expires_at=expires_at or (
                timezone.now() + timedelta(minutes=5)
            ),
            attempts=attempts,
            is_used=is_used
        )

    # 1. Test OTP generation
    def test_generate_otp(self):
        otp = generate_otp()

        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())

    # 2. Test OTP creation and email sending
    @patch("accounts.services.otp_services.send_otp_email")
    @patch("accounts.services.otp_services.generate_otp")
    def test_create_and_send_otp(self, mock_generate, mock_email):
        mock_generate.return_value = self.otp

        result = create_and_send_otp(
            self.user,
            self.purpose
        )

        self.assertTrue(result)

        otp_record = EmailOTP.objects.get(
            user=self.user,
            purpose=self.purpose
        )

        self.assertTrue(
            check_password(self.otp, otp_record.otp_hash)
        )

        mock_email.assert_called_once_with(
            self.user.email,
            self.otp,
            self.purpose
        )

    # 3. Test sending OTP to a different email
    @patch("accounts.services.otp_services.send_otp_email")
    @patch("accounts.services.otp_services.generate_otp")
    def test_send_otp_to_target_email(self, mock_generate, mock_email):
        mock_generate.return_value = self.otp
        target_email = "new@example.com"

        create_and_send_otp(
            self.user,
            self.purpose,
            target_email=target_email
        )

        mock_email.assert_called_once_with(
            target_email,
            self.otp,
            self.purpose
        )

    # 4. Test resend cooldown
    @patch("accounts.services.otp_services.send_otp_email")
    def test_otp_resend_cooldown(self, mock_email):
        self.create_otp()

        with self.assertRaises(ValidationError):
            create_and_send_otp(self.user, self.purpose)

        mock_email.assert_not_called()

    # 5. Test resend after cooldown
    @patch("accounts.services.otp_services.send_otp_email")
    @patch("accounts.services.otp_services.generate_otp")
    def test_resend_otp_after_cooldown(
        self, mock_generate, mock_email
    ):
        old_otp = self.create_otp()

        EmailOTP.objects.filter(pk=old_otp.pk).update(
            created_at=timezone.now() - timedelta(seconds=61)
        )

        mock_generate.return_value = "654321"

        create_and_send_otp(self.user, self.purpose)

        old_otp.refresh_from_db()

        self.assertTrue(old_otp.is_used)

        self.assertEqual(
            EmailOTP.objects.filter(
                user=self.user,
                purpose=self.purpose,
                is_used=False
            ).count(),
            1
        )

        mock_email.assert_called_once()

    # 6. Test email sending failure
    @patch(
        "accounts.services.otp_services.send_otp_email",
        side_effect=Exception("Email failed")
    )
    @patch("accounts.services.otp_services.generate_otp")
    def test_otp_email_failure(self, mock_generate, mock_email):
        mock_generate.return_value = self.otp

        with self.assertRaises(ValidationError):
            create_and_send_otp(self.user, self.purpose)

        self.assertEqual(
            EmailOTP.objects.filter(
                user=self.user,
                purpose=self.purpose
            ).count(),
            0
        )

    # 7. Test successful OTP verification
    def test_verify_otp_success(self):
        otp_record = self.create_otp()

        result = verify_otp(
            self.user,
            self.otp,
            self.purpose
        )

        self.assertEqual(result.pk, otp_record.pk)

        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_used)

    # 8. Test incorrect OTP
    def test_verify_wrong_otp(self):
        otp_record = self.create_otp()

        with self.assertRaises(ValidationError):
            verify_otp(self.user, "999999", self.purpose)

        otp_record.refresh_from_db()
        self.assertEqual(otp_record.attempts, 1)

    # 9. Test expired OTP
    def test_verify_expired_otp(self):
        otp_record = self.create_otp(
            expires_at=timezone.now() - timedelta(minutes=1)
        )

        with self.assertRaises(ValidationError):
            verify_otp(self.user, self.otp, self.purpose)

        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_used)

    # 10. Test maximum attempts
    def test_maximum_otp_attempts(self):
        otp_record = self.create_otp(attempts=4)

        with self.assertRaises(ValidationError):
            verify_otp(self.user, "999999", self.purpose)

        otp_record.refresh_from_db()

        self.assertEqual(otp_record.attempts, 5)
        self.assertTrue(otp_record.is_used)

    # 11. Test already exhausted attempts
    def test_otp_already_exceeded_attempts(self):
        otp_record = self.create_otp(attempts=5)

        with self.assertRaises(ValidationError):
            verify_otp(self.user, self.otp, self.purpose)

        otp_record.refresh_from_db()
        self.assertTrue(otp_record.is_used)

    # 12. Test OTP not found
    def test_verify_nonexistent_otp(self):
        with self.assertRaises(ValidationError):
            verify_otp(self.user, self.otp, self.purpose)
