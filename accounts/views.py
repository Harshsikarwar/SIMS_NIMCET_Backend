
from django.contrib.auth import authenticate, get_user_model

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from accounts.serializers import (
    UserRegistrationSerializer,
    EmailVerificationSerializer,
    ResendOTPSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailUpdateSerializer,
    LogoutSerializer,
)

from accounts.services.auth_services import (
    send_verification_otp,
    verify_email,
    resend_verification_otp,
    send_password_reset_otp,
    reset_password,
    send_email_update_otp,
    verify_email_update,
)

User = get_user_model()


# --------------------------------
# 1. USER REGISTRATION
# --------------------------------

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        send_verification_otp(user)

        return Response(
            {
                "message": "Registration successful. OTP sent to your email.",
                "email": user.email,
            },
            status=status.HTTP_201_CREATED
        )


# --------------------------------
# 2. EMAIL VERIFICATION
# --------------------------------

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        user = User.objects.filter(
            email__iexact=email
        ).first()

        if not user:
            raise ValidationError("Invalid verification request.")

        verify_email(user, otp)

        return Response(
            {"message": "Email verified successfully."},
            status=status.HTTP_200_OK
        )


# --------------------------------
# 3. RESEND OTP
# --------------------------------

class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        user = User.objects.filter(
            email__iexact=email
        ).first()

        if not user or user.is_verified:
            return Response(
                {"message": "If an eligible account exists, an OTP will be sent."},
                status=status.HTTP_200_OK
            )

        resend_verification_otp(user)

        return Response(
            {"message": "Verification OTP sent successfully."},
            status=status.HTTP_200_OK
        )


# --------------------------------
# 4. USER LOGIN
# --------------------------------

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(
            email__iexact=email
        ).first()

        if not user:
            raise ValidationError("Invalid email or password.")

        credentials = {
            User.USERNAME_FIELD: user.get_username(),
            "password": password,
        }

        authenticated_user = authenticate(
            request,
            **credentials
        )

        if not authenticated_user:
            raise ValidationError("Invalid email or password.")

        if not authenticated_user.is_verified:
            raise ValidationError("Please verify your email first.")

        refresh = RefreshToken.for_user(authenticated_user)

        return Response(
            {
                "message": "Login successful.",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": authenticated_user.id,
                    "username": authenticated_user.username,
                    "email": authenticated_user.email,
                    "first_name": authenticated_user.first_name,
                    "last_name": authenticated_user.last_name,
                }
            },
            status=status.HTTP_200_OK
        )


# --------------------------------
# 5. USER LOGOUT
# --------------------------------

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh = RefreshToken(
                serializer.validated_data["refresh"]
            )

            # Ensure the refresh token belongs to this user.
            if str(refresh["user_id"]) != str(request.user.pk):
                raise ValidationError("Invalid refresh token.")

            refresh.blacklist()

            return Response(
                {"message": "Logout successful."},
                status=status.HTTP_200_OK
            )

        except TokenError:
            raise ValidationError("Invalid or expired refresh token.")


# --------------------------------
# 6. PASSWORD RESET REQUEST
# --------------------------------

class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        user = User.objects.filter(
            email__iexact=email,
            is_active=True,
            is_verified=True
        ).first()

        if user:
            send_password_reset_otp(user)

        return Response(
            {
                "message": "If an eligible account exists, password reset instructions will be sent."
            },
            status=status.HTTP_200_OK
        )


# --------------------------------
# 7. PASSWORD RESET CONFIRM
# --------------------------------

class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(
            data=request.data
        )
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]
        new_password = serializer.validated_data["new_password"]

        user = User.objects.filter(
            email__iexact=email,
            is_active=True,
            is_verified=True
        ).first()

        if not user:
            raise ValidationError("Invalid password reset request.")

        reset_password(user, otp, new_password)

        return Response(
            {"message": "Password reset successful."},
            status=status.HTTP_200_OK
        )


# --------------------------------
# 8. EMAIL UPDATE REQUEST
# --------------------------------

class EmailUpdateRequestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_email = serializer.validated_data["new_email"]

        send_email_update_otp(
            request.user,
            new_email
        )

        return Response(
            {"message": "OTP sent to your new email address."},
            status=status.HTTP_200_OK
        )


# --------------------------------
# 9. EMAIL UPDATE VERIFICATION
# --------------------------------

class EmailUpdateVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        otp = serializer.validated_data["otp"]

        user = verify_email_update(
            request.user,
            otp
        )

        return Response(
            {
                "message": "Email updated successfully.",
                "email": user.email,
            },
            status=status.HTTP_200_OK
        )
