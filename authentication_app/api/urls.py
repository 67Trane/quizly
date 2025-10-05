from django.urls import path
from .views import (
    RegistrationView,
    LoginView,
    LogoutView,
    RefreshCookieView,

)

# URL routing for authentication and account management.
urlpatterns = [
    # User registration (creates a new account and sends activation email).
    path("register/", RegistrationView.as_view(), name="registration"),
    # User login (returns JWT access/refresh tokens in cookies).
    path("login/", LoginView.as_view(), name="login"),
    # # User logout (blacklists the refresh token and clears cookies).
    path("logout/", LogoutView.as_view(), name="logout"),
    # # Obtain a new access token using a valid refresh token (cookie-based).
    path("token/refresh/", RefreshCookieView.as_view(), name="token_refresh"),
]