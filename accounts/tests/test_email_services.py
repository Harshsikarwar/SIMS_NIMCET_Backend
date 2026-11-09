
from django.test import TestCase, override_settings
from django.core import mail
from django.conf import settings

from accounts.services.email_services import send_otp_email


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class EmailServiceTests(TestCase):

    def setUp(self):
        mail.outbox = []

        self.email = "harshsikarwar2005@gmailcom.com"
        self.otp = "123456"

    # 1. Email verification
    def test_send_verification_email(self):
        result = send_otp_email(
            self.email,
            self.otp,
            "email_verification"
        )

        self.assertEqual(result, 1)
        self.assertEqual(len(mail.outbox), 1)

        email = mail.outbox[0]

        self.assertEqual(
            email.subject,
            "Verify Your SIMS-NIMCET Account"
        )
        self.assertEqual(email.to, [self.email])
        self.assertIn(self.otp, email.body)
        self.assertIn("5 minutes", email.body)

    # 2. Password reset email
    def test_send_password_reset_email(self):
        send_otp_email(
            self.email,
            self.otp,
            "password_reset"
        )

        email = mail.outbox[0]

        self.assertEqual(
            email.subject,
            "SIMS-NIMCET Password Reset"
        )
        self.assertIn(self.otp, email.body)

    # 3. Email update verification
    def test_send_email_update_email(self):
        send_otp_email(
            self.email,
            self.otp,
            "email_update"
        )

        email = mail.outbox[0]

        self.assertEqual(
            email.subject,
            "Verify Your New Email Address"
        )
        self.assertIn(self.otp, email.body)

    # 4. Unknown purpose uses default subject
    def test_send_email_with_unknown_purpose(self):
        send_otp_email(
            self.email,
            self.otp,
            "unknown_purpose"
        )

        email = mail.outbox[0]

        self.assertEqual(
            email.subject,
            "SIMS-NIMCET Verification"
        )

    # 5. Default purpose
    def test_send_email_with_default_purpose(self):
        send_otp_email(
            self.email,
            self.otp
        )

        email = mail.outbox[0]

        self.assertEqual(
            email.subject,
            "Verify Your SIMS-NIMCET Account"
        )

    # 6. Check sender email
    def test_sender_email(self):
        send_otp_email(
            self.email,
            self.otp
        )

        email = mail.outbox[0]

        self.assertEqual(
            email.from_email,
            settings.DEFAULT_FROM_EMAIL
        )

    # 7. Check email content
    def test_email_contains_required_message(self):
        send_otp_email(
            self.email,
            self.otp
        )

        email = mail.outbox[0]

        self.assertIn("Hello,", email.body)
        self.assertIn("Your OTP for SIMS-NIMCET is:", email.body)
        self.assertIn("If you did not request this", email.body)
        self.assertIn("SIMS-NIMCET Team", email.body)
