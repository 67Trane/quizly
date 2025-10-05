from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from django.conf import settings
from .serializers import (
    RegistrationSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


class RegistrationView(APIView):
    permission_classes= [AllowAny]
    