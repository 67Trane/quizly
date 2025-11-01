import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    """Provides a DRF APIClient instance for making HTTP requests in tests."""
    return APIClient()


@pytest.fixture
def create_user(db):
    """
    Factory fixture to create users quickly in tests.

    Works with both custom and default User models. If the active User model
    doesn't have a 'username' field, it will be omitted automatically.
    """

    def _create_user(
        username="alice",
        email="alice@example.com",
        password="pass1234",
        **extra,
    ):
        # Determine available fields on the current User model (custom models may differ)
        field_names = {f.name for f in User._meta.get_fields()}

        # Build kwargs for create_user with required fields and any extra overrides
        kwargs = {"email": email, "password": password, **extra}
        if "username" in field_names:
            kwargs["username"] = username

        # Create the user via the model manager to ensure the password is hashed
        user = User.objects.create_user(**kwargs)
        return user

    return _create_user


@pytest.fixture
def user_token_pair(create_user):
    """
    Creates a user and returns a tuple of (access_token, refresh_token, user).

    Tokens are generated using SimpleJWT and can be used to authenticate requests
    in integration tests.
    """
    user = create_user()
    refresh = RefreshToken.for_user(user)  # Issue a refresh token for the user
    access = refresh.access_token  # Derive the corresponding access token
    return access, refresh, user
