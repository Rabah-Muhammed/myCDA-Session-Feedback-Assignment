from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import FamilyLink, User
from classes.models import Class, ClassEnrollment, Session
from feedback.models import SessionFeedback


class SessionFeedbackTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Users
        self.instructor = User.objects.create_user(
            username="coach.chen", email="chen@cda.test",
            password="testpass123", role="instructor",
            first_name="Sarah", last_name="Chen",
        )
        self.other_instructor = User.objects.create_user(
            username="coach.marcus", email="marcus@cda.test",
            password="testpass123", role="instructor",
            first_name="Marcus", last_name="Rivera",
        )
        self.admin = User.objects.create_user(
            username="admin.user", email="admin@cda.test",
            password="testpass123", role="admin",
        )
        self.parent = User.objects.create_user(
            username="parent.james", email="james@cda.test",
            password="testpass123", role="parent",
            first_name="James", last_name="Wilson",
        )
        self.other_parent = User.objects.create_user(
            username="parent.stranger", email="stranger@cda.test",
            password="testpass123", role="parent",
        )
        self.student = User.objects.create_user(
            username="student.emma", email="emma@cda.test",
            password="testpass123", role="student",
            first_name="Emma", last_name="Wilson",
        )
        self.other_student = User.objects.create_user(
            username="student.noah", email="noah@cda.test",
            password="testpass123", role="student",
        )

        # FamilyLink: James is parent of Emma
        FamilyLink.objects.create(parent=self.parent, student=self.student)

        # Class & Enrollments
        self.cls = Class.objects.create(
            name="Lincoln-Douglas Fundamentals",
            instructor=self.instructor,
        )
        ClassEnrollment.objects.create(class_obj=self.cls, student=self.student)
        ClassEnrollment.objects.create(class_obj=self.cls, student=self.other_student)

        # Sessions
        now = timezone.now()
        self.completed_session = Session.objects.create(
            class_obj=self.cls,
            scheduled_date=now - timedelta(days=5),
            status="completed",
            session_metadata={"duration_minutes": 60, "topic_covered": "Cross-ex"},
        )
        self.scheduled_session = Session.objects.create(
            class_obj=self.cls,
            scheduled_date=now + timedelta(days=2),
            status="scheduled",
            session_metadata={"duration_minutes": 60},
        )
        self.cancelled_session = Session.objects.create(
            class_obj=self.cls,
            scheduled_date=now - timedelta(days=3),
            status="cancelled",
            session_metadata={"duration_minutes": 60},
        )
        self.old_session = Session.objects.create(
            class_obj=self.cls,
            scheduled_date=now - timedelta(days=35),
            status="completed",
            session_metadata={"duration_minutes": 60},
        )

    def _auth(self, user):
        """Logs in user so both Django session middleware (RequestAuditMiddleware) and DRF know the user."""
        self.client.force_login(user)
        self.client.force_authenticate(user=user)

    # ---- Validation & Submission Tests ----

    def test_student_can_submit_feedback(self):
        self._auth(self.student)
        payload = {
            "session": self.completed_session.id,
            "rating_clarity": 5,
            "rating_engagement": 4,
            "rating_pace": 4,
            "notes": "Great practice session!",
        }
        response = self.client.post("/api/v1/feedback/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["student"], self.student.id)
        self.assertEqual(response.data["submitter"], self.student.id)

    def test_submitter_cannot_be_forged(self):
        """Submitter is auto-populated from request user, ignoring payload."""
        self._auth(self.student)
        payload = {
            "session": self.completed_session.id,
            "submitter": self.admin.id,  # Attempting to forge submitter
            "rating_clarity": 5,
            "rating_engagement": 5,
            "rating_pace": 5,
        }
        response = self.client.post("/api/v1/feedback/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["submitter"], self.student.id)

    def test_parent_can_submit_for_linked_student(self):
        self._auth(self.parent)
        payload = {
            "session": self.completed_session.id,
            "student": self.student.id,
            "rating_clarity": 4,
            "rating_engagement": 5,
            "rating_pace": 3,
            "notes": "Submitted by parent.",
        }
        response = self.client.post("/api/v1/feedback/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["student"], self.student.id)
        self.assertEqual(response.data["submitter"], self.parent.id)

    def test_parent_cannot_submit_for_unlinked_student(self):
        self._auth(self.other_parent)
        payload = {
            "session": self.completed_session.id,
            "student": self.student.id,
            "rating_clarity": 4,
            "rating_engagement": 4,
            "rating_pace": 4,
        }
        response = self.client.post("/api/v1/feedback/", payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("student", response.data)

    def test_cannot_submit_for_scheduled_session(self):
        self._auth(self.student)
        payload = {
            "session": self.scheduled_session.id,
            "rating_clarity": 5,
            "rating_engagement": 5,
            "rating_pace": 5,
        }
        response = self.client.post("/api/v1/feedback/", payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("session", response.data)

    def test_cannot_submit_for_cancelled_session(self):
        self._auth(self.student)
        payload = {
            "session": self.cancelled_session.id,
            "rating_clarity": 5,
            "rating_engagement": 5,
            "rating_pace": 5,
        }
        response = self.client.post("/api/v1/feedback/", payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("session", response.data)

    def test_cannot_submit_for_session_older_than_30_days(self):
        self._auth(self.student)
        payload = {
            "session": self.old_session.id,
            "rating_clarity": 5,
            "rating_engagement": 5,
            "rating_pace": 5,
        }
        response = self.client.post("/api/v1/feedback/", payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("session", response.data)

    def test_cannot_submit_duplicate_feedback(self):
        """Uniqueness on (session, student) prevents duplicate reviews."""
        # 1. First submission by student
        SessionFeedback.objects.create(
            session=self.completed_session,
            student=self.student,
            submitter=self.student,
            rating_clarity=4,
            rating_engagement=4,
            rating_pace=4,
        )

        # 2. Parent tries to submit for same student and session
        self._auth(self.parent)
        payload = {
            "session": self.completed_session.id,
            "student": self.student.id,
            "rating_clarity": 5,
            "rating_engagement": 5,
            "rating_pace": 5,
        }
        response = self.client.post("/api/v1/feedback/", payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_ratings_outside_1_to_5_rejected(self):
        self._auth(self.student)
        for bad_rating in [0, 6, -1]:
            payload = {
                "session": self.completed_session.id,
                "rating_clarity": bad_rating,
                "rating_engagement": 4,
                "rating_pace": 4,
            }
            response = self.client.post("/api/v1/feedback/", payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ---- History Endpoint Tests ----

    def test_student_history_list(self):
        SessionFeedback.objects.create(
            session=self.completed_session,
            student=self.student,
            submitter=self.student,
            rating_clarity=4,
            rating_engagement=5,
            rating_pace=4,
        )
        self._auth(self.student)
        response = self.client.get("/api/v1/feedback/my/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_parent_history_shows_linked_children(self):
        SessionFeedback.objects.create(
            session=self.completed_session,
            student=self.student,
            submitter=self.parent,
            rating_clarity=4,
            rating_engagement=5,
            rating_pace=4,
        )
        self._auth(self.parent)
        response = self.client.get("/api/v1/feedback/my/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    # ---- Instructor Summary & Math Tests ----

    def test_weighted_rolling_average_math(self):
        """
        Verify the exact rubric calculation:
        Session A: 90 min, avg clarity = 4.0
        Session B: 60 min, avg clarity = 3.0
        Weighted avg = (90*4.0 + 60*3.0) / (90 + 60) = 540 / 150 = 3.6
        (Not simple avg of 3.5)
        """
        now = timezone.now()
        session_a = Session.objects.create(
            class_obj=self.cls,
            scheduled_date=now - timedelta(days=2),
            status="completed",
            session_metadata={"duration_minutes": 90},
        )
        session_b = Session.objects.create(
            class_obj=self.cls,
            scheduled_date=now - timedelta(days=1),
            status="completed",
            session_metadata={"duration_minutes": 60},
        )

        SessionFeedback.objects.create(
            session=session_a, student=self.student, submitter=self.student,
            rating_clarity=4, rating_engagement=4, rating_pace=4,
        )
        SessionFeedback.objects.create(
            session=session_b, student=self.other_student, submitter=self.other_student,
            rating_clarity=3, rating_engagement=3, rating_pace=3,
        )

        self._auth(self.instructor)
        response = self.client.get("/api/v1/feedback/instructor-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["clarity_avg"], 3.6)
        self.assertEqual(response.data["engagement_avg"], 3.6)
        self.assertEqual(response.data["pace_avg"], 3.6)
        self.assertEqual(response.data["overall_avg"], 3.6)
        self.assertEqual(response.data["total_feedback_count"], 2)

    def test_instructor_summary_strict_anonymization(self):
        """Ensure no student IDs, names, emails, submitter info, or raw notes leak."""
        SessionFeedback.objects.create(
            session=self.completed_session,
            student=self.student,
            submitter=self.student,
            rating_clarity=5,
            rating_engagement=5,
            rating_pace=5,
            notes="Secret student note",
        )
        self._auth(self.instructor)
        response = self.client.get("/api/v1/feedback/instructor-summary/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        forbidden_keys = [
            "student", "student_id", "student_name", "student_email",
            "submitter", "submitter_id", "submitter_name",
            "note", "notes", "raw_notes",
        ]
        for key in forbidden_keys:
            self.assertNotIn(key, response.data)

    def test_admin_can_view_any_instructor_summary(self):
        self._auth(self.admin)
        response = self.client.get(
            f"/api/v1/feedback/instructor-summary/?instructor_id={self.instructor.id}"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_student_cannot_access_instructor_summary(self):
        self._auth(self.student)
        response = self.client.get("/api/v1/feedback/instructor-summary/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)