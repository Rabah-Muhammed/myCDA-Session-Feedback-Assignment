"""
Existing tests -- these must continue to pass after the candidate's changes.
"""

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from accounts.models import User, FamilyLink


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@cda.test",
            password="testpass123",
            first_name="Test",
            last_name="User",
            role="student",
        )

    def test_login_returns_token(self):
        response = self.client.post(
            "/api/v1/accounts/login/",
            {"username": "testuser", "password": "testpass123"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["role"], "student")

    def test_login_bad_password(self):
        response = self.client.post(
            "/api/v1/accounts/login/",
            {"username": "testuser", "password": "wrong"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_profile_requires_auth(self):
        response = self.client.get("/api/v1/accounts/profile/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_profile_returns_user_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/v1/accounts/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "test@cda.test")
        self.assertEqual(response.data["role"], "student")


class FamilyLinkTests(TestCase):
    def setUp(self):
        self.parent = User.objects.create_user(
            username="parent1", email="parent1@cda.test",
            password="testpass123", role="parent",
            first_name="Parent", last_name="One",
        )
        self.student = User.objects.create_user(
            username="student1", email="student1@cda.test",
            password="testpass123", role="student",
            first_name="Student", last_name="One",
        )
        FamilyLink.objects.create(
            parent=self.parent, student=self.student
        )

    def test_parent_profile_shows_family_links(self):
        client = APIClient()
        client.force_authenticate(user=self.parent)
        response = client.get("/api/v1/accounts/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("family_links", response.data)
        self.assertEqual(len(response.data["family_links"]), 1)
        self.assertEqual(
            response.data["family_links"][0]["student_display"]["role"],
            "student",
        )

    def test_student_profile_has_no_family_links_key(self):
        client = APIClient()
        client.force_authenticate(user=self.student)
        response = client.get("/api/v1/accounts/profile/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("family_links", response.data)

    def test_unique_family_link(self):
        """Cannot create duplicate family links."""
        with self.assertRaises(Exception):
            FamilyLink.objects.create(
                parent=self.parent, student=self.student
            )
