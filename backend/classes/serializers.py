from rest_framework import serializers
from core.serializers import BaseModelSerializer, ReadOnlyBaseSerializer
from accounts.serializers import UserMinimalSerializer
from .models import Class, ClassEnrollment, Session


class ClassSerializer(BaseModelSerializer):
    instructor_display = UserMinimalSerializer(
        source="instructor", read_only=True
    )
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = Class
        fields = [
            "id",
            "name",
            "description",
            "instructor",
            "instructor_display",
            "is_active",
            "student_count",
            "created_at",
            "updated_at",
        ]

    def get_student_count(self, obj):
        return obj.enrollments.filter(is_active=True).count()


class SessionSerializer(ReadOnlyBaseSerializer):
    class_name = serializers.CharField(source="class_obj.name", read_only=True)
    instructor_display = UserMinimalSerializer(
        source="class_obj.instructor", read_only=True
    )
    duration_minutes = serializers.IntegerField(read_only=True)
    topic = serializers.CharField(read_only=True)

    class Meta:
        model = Session
        fields = [
            "id",
            "class_obj",
            "class_name",
            "instructor_display",
            "scheduled_date",
            "status",
            "duration_minutes",
            "topic",
            "created_at",
            "updated_at",
        ]


class EnrollmentSerializer(ReadOnlyBaseSerializer):
    class_detail = ClassSerializer(source="class_obj", read_only=True)
    student_display = UserMinimalSerializer(source="student", read_only=True)

    class Meta:
        model = ClassEnrollment
        fields = [
            "id",
            "class_detail",
            "student_display",
            "enrolled_at",
            "is_active",
        ]
