from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import authenticate

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles user registration with password confirmation and validation.
    Ensures both passwords match and meet Django's password requirements.
    """

    confirmed_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirmed_password"]

    def validate(self, attrs):
        """
        Validates that both password fields match and that the password
        meets Django's built-in password strength requirements.
        """
        password = attrs.get("password")
        confirmed = attrs.get("confirmed_password")

        if password != confirmed:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwörter stimmen nicht überein."}
            )

        validate_password(password)
        return attrs

    def create(self, validated_data):
        """
        Creates a new user instance with a hashed password.
        Removes the confirmed_password field before saving.
        """
        validated_data.pop("confirmed_password", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """
    Handles user authentication by validating the provided credentials.
    Ensures the user exists, the password is correct, and the account is active.
    """

    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """
        Authenticates the user using Django's built-in authentication system.
        Raises a validation error if credentials are invalid or the user is inactive.
        """
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError("username or password is wrong")

        user = authenticate(username=username, password=password)

        if user is None:
            raise serializers.ValidationError("wrong username or password")

        if not user.is_active:
            raise serializers.ValidationError("account is inactive or banned")

        attrs["user"] = user
        return attrs
