import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


@pytest.fixture
def api_client():
    """DRF test client."""
    return APIClient()


@pytest.fixture
def create_user(db):
    """Factory to create users quickly."""
    def _create_user(
        username="alice",
        email="alice@example.com",
        password="pass1234",
        **extra,
    ):
        # If your Custom User has no 'username' field, drop it:
        field_names = {f.name for f in User._meta.get_fields()}
        kwargs = {"email": email, "password": password, **extra}
        if "username" in field_names:
            kwargs["username"] = username
        user = User.objects.create_user(**kwargs)
        return user
    return _create_user


@pytest.fixture
def user_token_pair(create_user):
    """Creates a user and returns (access, refresh, user)."""
    user = create_user()
    refresh = RefreshToken.for_user(user)
    access = refresh.access_token
    return access, refresh, user
