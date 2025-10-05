from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
from .serializers import (
    RegisterSerializer,
    LoginSerializer
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class RegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"detail": "User created successfully!"}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]


        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        access_max_age = int(access.lifetime.total_seconds())
        refresh_max_age = int(refresh.lifetime.total_seconds())

        secure = not settings.DEBUG
        samesite = "None" if not settings.DEBUG else "Lax"

        res = Response({
            "detail": "Login successfully!",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            }
        }, status=status.HTTP_200_OK)

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
