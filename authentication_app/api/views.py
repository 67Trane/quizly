from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from django.conf import settings
from .serializers import (
    RegisterSerializer,
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


access_token_time = 60*5     #  5 minutes
refresh_token_time = 60 * 60 * 24   #  1 day


class RegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({"detail": "User created successfully!"}, status=status.HTTP_201_CREATED)
    
    
# class LoginView(APIView):
#     permission_classes = [AllowAny]
#     authentication_classes = []