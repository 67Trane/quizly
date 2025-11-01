from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
from .serializers import RegisterSerializer, LoginSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class RegistrationView(APIView):
    """
    Public endpoint to register a new user account.
    Uses RegisterSerializer to validate and create the user.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # No auth required for registration

    def post(self, request):
        """
        Validate incoming payload and create a user.
        Returns 201 on success.
        """
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"detail": "User created successfully!"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Public endpoint to authenticate a user.
    On success, issues JWT access/refresh tokens in HttpOnly cookies.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # No auth required for login

    def post(self, request):
        """
        Authenticate credentials and set signed JWT cookies.
        Access token is short-lived; refresh token is longer-lived.
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # Create refresh and access tokens for the authenticated user
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # Convert lifetimes to cookie max-age (in seconds)
        access_max_age = int(access.lifetime.total_seconds())
        refresh_max_age = int(refresh.lifetime.total_seconds())

        # Use secure cookies in production; SameSite=None requires 'secure=True'
        secure = not settings.DEBUG
        samesite = "None" if not settings.DEBUG else "Lax"

        # Build response body with minimal user info
        res = Response(
            {
                "detail": "Login successfully!",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
            },
            status=status.HTTP_200_OK,
        )

        # Set HttpOnly cookies to mitigate XSS; tokens are not accessible via JS
        res.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=secure,
            samesite=samesite,
            max_age=access_max_age,
            path="/",
        )
        res.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=secure,
            samesite=samesite,
            max_age=refresh_max_age,
            path="/",
        )
        return res


class LogoutView(APIView):
    """
    Authenticated endpoint to log out the current user.
    Clears authentication cookies on the client.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Delete access/refresh cookies from the client.
        Note: If using a token blacklist, you may also blacklist the refresh token here.
        """
        res = Response(
            {
                "detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."
            },
            status=status.HTTP_200_OK,
        )
        # Remove both tokens from the client
        res.delete_cookie("access_token", path="/")
        res.delete_cookie("refresh_token", path="/")
        return res


class RefreshCookieView(APIView):
    """
    Public endpoint to rotate/refresh the access token using the refresh token cookie.
    """

    permission_classes = [AllowAny]
    authentication_classes = []  # Refresh by cookie, not by auth header

    def post(self, request):
        """
        Issue a new access token if the refresh token cookie is present and valid.
        Returns 401 if missing/invalid.
        """
        token = request.COOKIES.get("refresh_token")
        if not token:
            return Response(
                {"detail": "refresh token not avialable"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        try:
            # Validate/parse the refresh token
            refresh = RefreshToken(token)
        except TokenError:
            return Response(
                {"detail": "refresh token not valid or expired"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Create a fresh access token from the valid refresh token
        access = refresh.access_token

        access_max_age = int(access.lifetime.total_seconds())
        secure = not settings.DEBUG
        samesite = "None" if not settings.DEBUG else "Lax"

        res = Response(
            {"detail": "Token refreshed", "access": str(access)},
            status=status.HTTP_200_OK,
        )
        # Update the access token cookie
        res.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=secure,
            samesite=samesite,
            max_age=access_max_age,
            path="/",
        )
        return res
