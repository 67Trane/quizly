import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

# ---------- RegistrationView ----------


@pytest.mark.django_db
def test_registration_success(api_client):
    """Creates a new user and returns HTTP 201 with a success detail message."""
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
    """
    Returns HTTP 400 when password confirmation fails
    (or when password validation rejects the input).
    """
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
    """
    On successful login with DEBUG=False, sets HttpOnly, Secure cookies
    for 'access_token' and 'refresh_token' with SameSite=None and returns user info.
    """
    user = create_user(username="bob", email="bob@example.com", password="pass1234")
    url = reverse("login")
    payload = {"username": "bob", "password": "pass1234"}

    # Simulate production-like settings: secure cookies + SameSite=None
    settings.DEBUG = False

    res = api_client.post(url, payload, format="json")
    assert res.status_code == status.HTTP_200_OK
    assert res.data["detail"] == "Login successfully!"

    # Validate minimal user payload
    assert res.data["user"]["id"] == user.id
    assert res.data["user"]["username"] == "bob"
    assert res.data["user"]["email"] == "bob@example.com"

    # Ensure cookies exist and carry proper flags
    cookies = res.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies

    access_cookie = cookies["access_token"]
    refresh_cookie = cookies["refresh_token"]

    # Must be HttpOnly and Secure in non-debug
    assert access_cookie["httponly"]
    assert refresh_cookie["httponly"]
    assert access_cookie["secure"] is True
    assert refresh_cookie["secure"] is True
    # SameSite=None is required for cross-site cookie usage with Secure=True
    assert access_cookie["samesite"] == "None"
    assert refresh_cookie["samesite"] == "None"


@pytest.mark.django_db
def test_login_debug_mode_cookie_flags(api_client, create_user, settings):
    """
    In DEBUG=True, cookies should not be Secure and should use SameSite=Lax,
    which is convenient for local development on http://localhost.
    """
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
    """
    Returns 400/401 on invalid credentials. The exact status code depends on
    serializer behavior; both are acceptable for this test.
    """
    url = reverse("login")
    payload = {"username": "unknown", "password": "wrong"}
    res = api_client.post(url, payload, format="json")
    assert res.status_code in (
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED,
    )


# ---------- LogoutView ----------


@pytest.mark.django_db
def test_logout_requires_auth(api_client):
    """Requires authentication; returns 401/403 when no credentials are provided."""
    url = reverse("logout")
    res = api_client.post(url, format="json")
    assert res.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


@pytest.mark.django_db
def test_logout_deletes_cookies(api_client, user_token_pair):
    """
    With a valid Authorization header, logout should delete the cookies by
    setting Max-Age=0 for both 'access_token' and 'refresh_token'.
    """
    access, refresh, _user = user_token_pair
    url = reverse("logout")

    # Simulate existing cookies on the client
    api_client.cookies["access_token"] = str(access)
    api_client.cookies["refresh_token"] = str(refresh)

    res = api_client.post(
        url, format="json", HTTP_AUTHORIZATION=f"Bearer {str(access)}"
    )
    assert res.status_code == status.HTTP_200_OK

    # Django's response renders deleted cookies with max-age=0
    assert "access_token" in res.cookies
    assert res.cookies["access_token"]["max-age"] == 0
    assert "refresh_token" in res.cookies
    assert res.cookies["refresh_token"]["max-age"] == 0


# ---------- RefreshCookieView ----------


@pytest.mark.django_db
def test_refresh_without_cookie_returns_401(api_client):
    """Returns 401 when the 'refresh_token' cookie is missing."""
    url = reverse("token_refresh")
    res = api_client.post(url, format="json")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "refresh token not avialable" in res.data["detail"]


@pytest.mark.django_db
def test_refresh_with_invalid_token_returns_401(api_client):
    """Returns 401 when the refresh token in the cookie is invalid or malformed."""
    url = reverse("token_refresh")
    api_client.cookies["refresh_token"] = "invalid.token.here"
    res = api_client.post(url, format="json")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "refresh token not valid or expired" in res.data["detail"]


@pytest.mark.django_db
def test_refresh_with_valid_cookie_sets_access_cookie(
    api_client, create_user, settings
):
    """
    With a valid refresh token cookie and DEBUG=False, returns 200, includes a fresh
    access token in the response body, and sets an HttpOnly, Secure, SameSite=None
    'access_token' cookie.
    """
    user = create_user()
    refresh = RefreshToken.for_user(user)
    url = reverse("token_refresh")

    # Client sends refresh token via cookie
    api_client.cookies["refresh_token"] = str(refresh)

    settings.DEBUG = False

    res = api_client.post(url, format="json")
    assert res.status_code == status.HTTP_200_OK
    assert res.data["detail"] == "Token refreshed"

    # Response body should contain a string access token
    assert "access" in res.data and isinstance(res.data["access"], str)

    # Cookie should be updated with correct flags
    assert "access_token" in res.cookies
    access_cookie = res.cookies["access_token"]
    assert access_cookie["httponly"]
    assert access_cookie["secure"] is True
    assert access_cookie["samesite"] == "None"
