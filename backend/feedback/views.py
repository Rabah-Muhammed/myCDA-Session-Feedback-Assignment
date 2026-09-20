from datetime import timedelta
from django.db.models import Avg
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import FamilyLink, User
from classes.models import ClassEnrollment, Session
from core.permissions import IsInstructorOrAdmin, IsStudentOrParent
from .models import SessionFeedback
from .serializers import (
    InstructorSummarySerializer,
    SessionFeedbackSerializer,
)


class FeedbackCreateView(generics.CreateAPIView):
    """
    POST /api/v1/feedback/
    Submit session feedback. Available to students and parents.
    """

    serializer_class = SessionFeedbackSerializer
    permission_classes = [IsStudentOrParent]


class MyFeedbackListView(generics.ListAPIView):
    """
    GET /api/v1/feedback/my/
    List feedback submitted by current student, or for a parent's linked students.
    Ordered by most recent first. Paginated.
    """

    serializer_class = SessionFeedbackSerializer
    permission_classes = [IsStudentOrParent]

    def get_queryset(self):
        user = self.request.user
        if user.role == "student":
            return (
                SessionFeedback.objects.filter(student=user)
                .select_related("session", "session__class_obj", "student", "submitter")
                .order_by("-created_at")
            )
        elif user.role == "parent":
            children_ids = FamilyLink.objects.filter(parent=user).values_list(
                "student_id", flat=True
            )
            return (
                SessionFeedback.objects.filter(student_id__in=children_ids)
                .select_related("session", "session__class_obj", "student", "submitter")
                .order_by("-created_at")
            )
        return SessionFeedback.objects.none()


class EligibleSessionsView(APIView):
    """
    GET /api/v1/feedback/eligible-sessions/?student_id=X
    Returns sessions eligible for feedback:
    - Status is 'completed'
    - Within the last 30 days
    - Student is enrolled in the class
    - Not yet reviewed for this student
    """

    permission_classes = [IsStudentOrParent]

    def get(self, request):
        user = request.user
        target_student = user

        if user.role == "parent":
            student_id = request.query_params.get("student_id")
            if not student_id:
                return Response(
                    {"error": "student_id query parameter is required for parents."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                target_student = User.objects.get(id=student_id, role="student")
            except User.DoesNotExist:
                return Response(
                    {"error": "Student not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Ensure parent is linked to this student
            if not FamilyLink.objects.filter(parent=user, student=target_student).exists():
                return Response(
                    {"error": "You are not authorized for this student."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        # Classes student is enrolled in
        enrolled_class_ids = ClassEnrollment.objects.filter(
            student=target_student, is_active=True
        ).values_list("class_obj_id", flat=True)

        # Completed sessions in last 30 days
        cutoff = timezone.now() - timedelta(days=30)
        completed_sessions = Session.objects.filter(
            class_obj_id__in=enrolled_class_ids,
            status="completed",
            scheduled_date__gte=cutoff,
        ).select_related("class_obj", "class_obj__instructor")

        # Exclude sessions already reviewed by/for this student
        reviewed_session_ids = SessionFeedback.objects.filter(
            student=target_student
        ).values_list("session_id", flat=True)

        eligible = completed_sessions.exclude(id__in=reviewed_session_ids)

        data = [
            {
                "id": s.id,
                "class_id": s.class_obj.id,
                "class_name": s.class_obj.name,
                "instructor_name": s.class_obj.instructor.get_display_name(),
                "scheduled_date": s.scheduled_date,
                "topic": s.topic,
                "duration_minutes": s.duration_minutes,
            }
            for s in eligible
        ]
        return Response(data, status=status.HTTP_200_OK)


class InstructorSummaryView(APIView):
    """
    GET /api/v1/feedback/instructor-summary/
    Available to instructors and admins.
    Calculates the manual duration-weighted rolling average of the last 10 completed sessions.
    Strictly anonymized: no student names, IDs, emails, submitter info, or notes.
    """
    permission_classes = [IsInstructorOrAdmin]
    def get(self, request):
        user = request.user
        instructor_id = request.query_params.get("instructor_id")
        if user.role == "admin" and instructor_id:
            try:
                instructor = User.objects.get(id=instructor_id, role="instructor")
            except User.DoesNotExist:
                return Response(
                    {"error": "Instructor not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        elif user.role == "instructor":
            instructor = user
        elif user.role == "admin" and not instructor_id:
            return Response(
                {"error": "Admins must specify ?instructor_id=X."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            return Response(
                {"error": "Unauthorized access."},
                status=status.HTTP_403_FORBIDDEN,
            )
        # 1. Fetch the last 10 completed sessions for this instructor
        last_10_sessions = list(
            Session.objects.filter(
                class_obj__instructor=instructor,
                status="completed",
            ).order_by("-scheduled_date")[:10]
        )
        total_weight = 0.0
        weighted_clarity_sum = 0.0
        weighted_engagement_sum = 0.0
        weighted_pace_sum = 0.0
        total_feedback_count = 0
        sessions_with_feedback_count = 0
        # 2. Compute averages manually per session, then weight by duration
        for session in last_10_sessions:
            feedbacks = list(session.feedbacks.all())
            count = len(feedbacks)
            if count == 0:
                continue
            total_feedback_count += count
            sessions_with_feedback_count += 1
            
            # Read duration explicitly from session_metadata (fallback to 60)
            duration = float(session.session_metadata.get("duration_minutes", 60))
            
            # Manual sums for this session
            clarity_sum = sum(f.rating_clarity for f in feedbacks)
            engagement_sum = sum(f.rating_engagement for f in feedbacks)
            pace_sum = sum(f.rating_pace for f in feedbacks)
            
            # Session-level manual averages
            s_avg_clarity = clarity_sum / count
            s_avg_engagement = engagement_sum / count
            s_avg_pace = pace_sum / count
            
            # Weight by duration
            weighted_clarity_sum += s_avg_clarity * duration
            weighted_engagement_sum += s_avg_engagement * duration
            weighted_pace_sum += s_avg_pace * duration
            total_weight += duration
            
        # 3. Calculate final weighted rolling averages
        if total_weight > 0:
            clarity_avg = round(weighted_clarity_sum / total_weight, 2)
            engagement_avg = round(weighted_engagement_sum / total_weight, 2)
            pace_avg = round(weighted_pace_sum / total_weight, 2)
            overall_avg = round(
                (clarity_avg + engagement_avg + pace_avg) / 3.0, 2
            )
        else:
            clarity_avg = 0.0
            engagement_avg = 0.0
            pace_avg = 0.0
            overall_avg = 0.0
        summary_data = {
            "clarity_avg": clarity_avg,
            "engagement_avg": engagement_avg,
            "pace_avg": pace_avg,
            "overall_avg": overall_avg,
            "total_feedback_count": total_feedback_count,
            "sessions_evaluated": sessions_with_feedback_count,
        }
        # Validate with dedicated anonymizing serializer
        serializer = InstructorSummarySerializer(summary_data)
        return Response(serializer.data, status=status.HTTP_200_OK)