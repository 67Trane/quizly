from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import authenticate

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    confirmed_password = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirmed_password"]

    def validate(self, attrs):
        password = attrs.get("password")
        confirmed = attrs.get("confirmed_password")

        if password != confirmed:
            raise serializers.ValidationError({"confirmed_password": "Passwörter stimmen nicht überein."})

        validate_password(password)
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirmed_password", None)
        password = validated_data.pop("password")
        user = User.objects.create_user(password=password, **validated_data)
        return user
    
    
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        password = attrs.get("password")
        username = attrs.get("username")
        
        if not username or not password:
            raise serializers.ValidationError("username or password is wrong")
        
        user = authenticate(username=username, password=password)
        
        if user is None:
            raise serializers.ValidationError("wrong username or password")
            
        if not user.is_active:
            raise serializers.ValidationError("account is inactiv or banned")
        
        attrs["user"] = user
        
        return attrs