from django.urls import path
from .views import (
    RegistrationView,
    LoginView,
    LogoutView,
    RefreshCookieView,
)

"""
Defines URL routes for user authentication and account management.
Each route corresponds to a specific authentication action handled by its view.
"""

urlpatterns = [
    # Handles user registration (creates a new account and sends activation email)
    path("register/", RegistrationView.as_view(), name="registration"),
    # Handles user login and returns JWT access/refresh tokens via cookies
    path("login/", LoginView.as_view(), name="login"),
    # Handles user logout by blacklisting the refresh token and clearing cookies
    path("logout/", LogoutView.as_view(), name="logout"),
    # Provides a new access token using a valid refresh token (cookie-based)
    path("token/refresh/", RefreshCookieView.as_view(), name="token_refresh"),
]
