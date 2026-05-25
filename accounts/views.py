from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .permissions import IsAdminOrHead, IsManager, IsStaffMember
from .serializers import (
    ChangePasswordSerializer,
    CustomTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    # Login needs only credentials; role and redirect target come from the user record.
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [AllowAny]


class RegisterView(generics.CreateAPIView):
    # Anyone can register, but the account stays inactive until approval.
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response({
            "user": UserSerializer(user).data,
            "message": "Registration successful. Wait for admin or head approval before login.",
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data.get('refresh'))
            token.blacklist()
            return Response({"message": "Logged out."})
        except Exception:
            return Response({"error": "Invalid token."}, status=400)


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response({"error": "Old password incorrect."}, status=400)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({"message": "Password changed."})


class AdminUserListView(generics.ListCreateAPIView):
    # Admin/head can list users and create users directly.
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHead]


class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    # Admin/head can view, update, or delete one user.
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminOrHead]


class AdminChangeRoleView(APIView):
    # Admin/head can change a user's role after registration.
    permission_classes = [IsAuthenticated, IsAdminOrHead]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)
        new_role = request.data.get('role')
        valid = [r[0] for r in User.Role.choices]
        if new_role not in valid:
            return Response({"error": f"Invalid role. Choose: {valid}"}, status=400)
        user.role = new_role
        user.save()
        return Response({"message": f"Role set to {new_role}"})


class AdminActivateUserView(APIView):
    # Admin/head approval lets the user log in.
    permission_classes = [IsAuthenticated, IsAdminOrHead]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({
            "message": "User approved and activated.",
            "user": UserSerializer(user).data,
        })


class ManagerDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsManager]

    def get(self, request):
        return Response({"message": "Manager dashboard", "role": request.user.role})


class StaffResourceView(APIView):
    permission_classes = [IsAuthenticated, IsStaffMember]

    def get(self, request):
        return Response({"message": "Staff resource", "role": request.user.role})
