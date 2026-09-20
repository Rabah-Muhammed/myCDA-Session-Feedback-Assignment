from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers

from accounts.models import FamilyLink, User
from accounts.serializers import UserMinimalSerializer
from core.middleware import get_current_user
from core.serializers import BaseModelSerializer
from .models import SessionFeedback


class SessionFeedbackSerializer(BaseModelSerializer):
    """
    Serializer for creating and viewing session feedback.
    Follows project conventions by extending BaseModelSerializer.
    """

    submitter_display = UserMinimalSerializer(source="submitter", read_only=True)
    student_display = UserMinimalSerializer(source="student", read_only=True)
    class_name = serializers.CharField(
        source="session.class_obj.name", read_only=True
    )
    session_date = serializers.DateTimeField(
        source="session.scheduled_date", read_only=True
    )
    student = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role="student"),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = SessionFeedback
        fields = [
            "id",
            "session",
            "student",
            "student_display",
            "submitter",
            "submitter_display",
            "class_name",
            "session_date",
            "rating_clarity",
            "rating_engagement",
            "rating_pace",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "submitter",
            "created_at",
            "updated_at",
        ]
        validators = []  # Handled in validate() to allow student to default to logged-in user

    def validate(self, attrs):
        request_user = get_current_user()
        if not request_user or not request_user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        session = attrs.get("session")
        student = attrs.get("student")

        # 1. Handle student identification based on submitter role
        if request_user.role == "student":
            # Students can only submit for themselves
            if student and student != request_user:
                raise serializers.ValidationError(
                    {"student": "Students can only submit feedback for themselves."}
                )
            attrs["student"] = request_user
            student = request_user
        elif request_user.role == "parent":
            if not student:
                raise serializers.ValidationError(
                    {"student": "Parent must specify which linked student this feedback is for."}
                )
            # Verify FamilyLink exists
            is_linked = FamilyLink.objects.filter(
                parent=request_user, student=student
            ).exists()
            if not is_linked:
                raise serializers.ValidationError(
                    {"student": "You are not authorized to submit feedback for this student."}
                )
        else:
            raise serializers.ValidationError("Only students and parents can submit feedback.")

        # 2. Check session status
        if session.status != "completed":
            raise serializers.ValidationError(
                {"session": f"Feedback can only be submitted for completed sessions (status is '{session.status}')."}
            )

        # 3. Check 30-day window
        cutoff_date = timezone.now() - timedelta(days=30)
        if session.scheduled_date < cutoff_date:
            raise serializers.ValidationError(
                {"session": "Feedback cannot be submitted for sessions completed more than 30 days ago."}
            )

        # 4. Check uniqueness constraint: (session, student)
        # Check in validation for user-friendly error response before hitting DB constraint
        exists = SessionFeedback.objects.filter(
            session=session, student=student
        ).exists()
        if exists:
            raise serializers.ValidationError(
                {"non_field_errors": ["Feedback has already been submitted for this student and session."]}
            )

        return attrs

    def create(self, validated_data):
        # Auto-populate submitter from thread-local user
        user = get_current_user()
        validated_data["submitter"] = user
        return super().create(validated_data)


class InstructorSummarySerializer(serializers.Serializer):
    """
    Dedicated serializer for instructor rolling feedback summary.
    Strictly anonymized: NO student IDs, names, emails, submitter info, or raw notes.
    """

    clarity_avg = serializers.FloatField()
    engagement_avg = serializers.FloatField()
    pace_avg = serializers.FloatField()
    overall_avg = serializers.FloatField()
    total_feedback_count = serializers.IntegerField()
    sessions_evaluated = serializers.IntegerField()