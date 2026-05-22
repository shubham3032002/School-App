from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        request = self.context.get("request")
        user = authenticate(
            request=request,
            email=attrs["email"],
            password=attrs["password"],
        )

        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account is disabled.")

        role = getattr(user, "role", None)
        if role is None:
            raise serializers.ValidationError("This user does not have a role.")

        refresh = RefreshToken.for_user(user)
        refresh["role"] = role.role
        refresh["email"] = user.email

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "role": role.role,
            },
        }


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    full_name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    role = serializers.SerializerMethodField()

    def get_role(self, user):
        role = getattr(user, "role", None)
        return role.role if role else None


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate_refresh(self, value):
        try:
            self.token = RefreshToken(value)
        except Exception as exc:
            raise serializers.ValidationError("Invalid refresh token.") from exc
        return value

    def save(self, **kwargs):
        self.token.blacklist()


class CustomTokenRefreshSerializer(TokenRefreshSerializer):
    pass
