from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.utils import timezone

from accounts.models import User
from classes.models import Class, ClassEnrollment, Session


class ClassListTests(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            username="instr", email="instr@cda.test",
            password="testpass123", role="instructor",
        )
        self.student = User.objects.create_user(
            username="stud", email="stud@cda.test",
            password="testpass123", role="student",
        )
        self.other_student = User.objects.create_user(
            username="other", email="other@cda.test",
            password="testpass123", role="student",
        )
        self.cls = Class.objects.create(
            name="Test Class", instructor=self.instructor
        )
        ClassEnrollment.objects.create(
            class_obj=self.cls, student=self.student
        )

    def test_instructor_sees_own_classes(self):
        client = APIClient()
        client.force_authenticate(user=self.instructor)
        response = client.get("/api/v1/classes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_student_sees_enrolled_classes(self):
        client = APIClient()
        client.force_authenticate(user=self.student)
        response = client.get("/api/v1/classes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_unenrolled_student_sees_nothing(self):
        client = APIClient()
        client.force_authenticate(user=self.other_student)
        response = client.get("/api/v1/classes/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)


class SessionTests(TestCase):
    def setUp(self):
        self.instructor = User.objects.create_user(
            username="instr2", email="instr2@cda.test",
            password="testpass123", role="instructor",
        )
        self.cls = Class.objects.create(
            name="Session Test Class", instructor=self.instructor
        )
        self.session = Session.objects.create(
            class_obj=self.cls,
            scheduled_date=timezone.now(),
            status="completed",
            session_metadata={
                "duration_minutes": 75,
                "topic_covered": "Test topic",
            },
        )

    def test_session_duration_property(self):
        self.assertEqual(self.session.duration_minutes, 75)

    def test_session_topic_property(self):
        self.assertEqual(self.session.topic, "Test topic")

    def test_session_default_duration(self):
        s = Session.objects.create(
            class_obj=self.cls,
            scheduled_date=timezone.now(),
            status="completed",
            session_metadata={},
        )
        self.assertEqual(s.duration_minutes, 60)
