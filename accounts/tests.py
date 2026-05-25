from rest_framework.test import APITestCase

from .models import User


class SignupViewTests(APITestCase):
    def test_register_creates_inactive_user_without_tokens(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "fullname": "Signup Test",
                "username": "signup-test",
                "email": "signup-test@example.com",
                "role": "staff",
                "password": "StrongPass123!",
                "password2": "StrongPass123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertNotIn("tokens", response.data)
        self.assertEqual(response.data["user"]["email"], "signup-test@example.com")
        self.assertEqual(response.data["user"]["role"], "staff")
        self.assertFalse(response.data["user"]["is_active"])

        user = User.objects.get(email="signup-test@example.com")
        self.assertTrue(user.check_password("StrongPass123!"))
        self.assertEqual(user.role, User.Role.STAFF)
        self.assertFalse(user.is_active)
