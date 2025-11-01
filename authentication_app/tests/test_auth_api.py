import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

# ---------- RegistrationView ----------


@pytest.mark.django_db
def test_registration_success(api_client):
    """Should create a new user and return 201."""
    url = reverse("registration")
    payload = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "StrongPassw0rd!",
        "confirmed_password": "StrongPassw0rd!",
    }
    res = api_client.post(url, payload, format="json")
    assert res.status_code == status.HTTP_201_CREATED
    assert res.data["detail"] == "User created successfully!"


@pytest.mark.django_db
def test_registration_validation_error(api_client):
    """Should fail when passwords don't match or validation fails."""
    url = reverse("registration")
    payload = {
        "username": "baduser",
        "email": "bad@example.com",
        "password": "a",
        "confirmed_password": "b",
    }
    res = api_client.post(url, payload, format="json")
    assert res.status_code == status.HTTP_400_BAD_REQUEST



# ---------- LoginView ----------

@pytest.mark.django_db
def test_login_sets_tokens_as_cookies(api_client, create_user, settings):
    """Login should set access_token and refresh_token cookies and return user info."""
    user = create_user(
        username="bob", email="bob@example.com", password="pass1234")
    url = reverse("login")
    payload = {"username": "bob", "password": "pass1234"}


    settings.DEBUG = False

    res = api_client.post(url, payload, format="json")
    assert res.status_code == status.HTTP_200_OK
    assert res.data["detail"] == "Login successfully!"

    assert res.data["user"]["id"] == user.id
    assert res.data["user"]["username"] == "bob"
    assert res.data["user"]["email"] == "bob@example.com"


    cookies = res.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies


    access_cookie = cookies["access_token"]
    refresh_cookie = cookies["refresh_token"]


    assert access_cookie["httponly"]  # HttpOnly
    assert refresh_cookie["httponly"]
    assert access_cookie["secure"] is True
    assert refresh_cookie["secure"] is True
    assert access_cookie["samesite"] == "None"
    assert refresh_cookie["samesite"] == "None"


@pytest.mark.django_db
def test_login_debug_mode_cookie_flags(api_client, create_user, settings):
    """In DEBUG=True, cookies should be SameSite=Lax and secure flag not set."""
    create_user(username="dev", email="dev@example.com", password="pass1234")
    url = reverse("login")
    payload = {"username": "dev", "password": "pass1234"}

    settings.DEBUG = True

    res = api_client.post(url, payload, format="json")
    assert res.status_code == status.HTTP_200_OK

    access_cookie = res.cookies["access_token"]
    refresh_cookie = res.cookies["refresh_token"]

    assert not access_cookie["secure"]
    assert not refresh_cookie["secure"]

    assert access_cookie["samesite"] == "Lax"
    assert refresh_cookie["samesite"] == "Lax"


@pytest.mark.django_db
def test_login_invalid_credentials(api_client):
    """Should return 400 for invalid credentials (depends on your LoginSerializer)."""
    url = reverse("login")
    payload = {"username": "unknown", "password": "wrong"}
    res = api_client.post(url, payload, format="json")
    assert res.status_code in (
        status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED)


# ---------- LogoutView ----------

@pytest.mark.django_db
def test_logout_requires_auth(api_client):
    """Logout should return 401 when not authenticated."""
    url = reverse("logout")
    res = api_client.post(url, format="json")
    assert res.status_code in (
        status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_logout_deletes_cookies(api_client, user_token_pair):
    """
    With valid Authorization header, Logout should delete cookies.
    Note: Your LogoutView uses IsAuthenticated, so we authenticate via header.
    """
    access, refresh, user = user_token_pair
    url = reverse("logout")


    api_client.cookies["access_token"] = str(access)
    api_client.cookies["refresh_token"] = str(refresh)

    res = api_client.post(url, format="json",
                          HTTP_AUTHORIZATION=f"Bearer {str(access)}")
    assert res.status_code == status.HTTP_200_OK

    assert "access_token" in res.cookies
    assert res.cookies["access_token"]["max-age"] == 0
    assert "refresh_token" in res.cookies
    assert res.cookies["refresh_token"]["max-age"] == 0


# ---------- RefreshCookieView ----------

@pytest.mark.django_db
def test_refresh_without_cookie_returns_401(api_client):
    """No refresh_token cookie -> 401."""
    url = reverse("token_refresh")
    res = api_client.post(url, format="json")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "refresh token not avialable" in res.data["detail"]


@pytest.mark.django_db
def test_refresh_with_invalid_token_returns_401(api_client):
    """Invalid refresh token in cookie -> 401."""
    url = reverse("token_refresh")
    api_client.cookies["refresh_token"] = "invalid.token.here"
    res = api_client.post(url, format="json")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "refresh token not valid or expired" in res.data["detail"]


@pytest.mark.django_db
def test_refresh_with_valid_cookie_sets_access_cookie(api_client, create_user, settings):
    """
    Valid refresh cookie should generate a fresh access token cookie and return 200.
    """
    user = create_user()
    refresh = RefreshToken.for_user(user)
    url = reverse("token_refresh")

    api_client.cookies["refresh_token"] = str(refresh)


    settings.DEBUG = False

    res = api_client.post(url, format="json")
    assert res.status_code == status.HTTP_200_OK
    assert res.data["detail"] == "Token refreshed"

    assert "access" in res.data and isinstance(res.data["access"], str)

    assert "access_token" in res.cookies
    access_cookie = res.cookies["access_token"]
    assert access_cookie["httponly"]
    assert access_cookie["secure"] is True
    assert access_cookie["samesite"] == "None"
