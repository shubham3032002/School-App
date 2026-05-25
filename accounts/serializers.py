from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    # Frontend can redirect after login using the user's saved role.
    role_redirects = {
        'admin': '/admin/users/',
        'head': '/admin/users/',
        'manager': '/manager/dashboard/',
        'staff': '/staff/resource/',
    }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role']     = user.role
        token['email']    = user.email
        token['fullname'] = user.fullname
        token['username'] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        data['redirect_to'] = self.role_redirects.get(self.user.role, '/')
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ['email', 'username', 'fullname', 'role', 'password', 'password2']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        # Registered users stay inactive until admin/head approval.
        validated_data.pop('password2')
        validated_data['is_active'] = False
        return User.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'email', 'username', 'fullname', 'role', 'is_active', 'created_at']
        read_only_fields = ['id', 'email', 'role', 'is_active', 'created_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True,
                                         validators=[validate_password])
