from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from core.permissions import IsStudentOrParent, IsInstructorOrAdmin
from accounts.models import FamilyLink
from .models import Class, Session, ClassEnrollment
from .serializers import ClassSerializer, SessionSerializer, EnrollmentSerializer


class ClassListView(generics.ListAPIView):
    """List classes relevant to the current user."""

    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "instructor":
            return Class.objects.filter(
                instructor=user, is_active=True
            ).prefetch_related("enrollments")
        elif user.role == "student":
            return Class.objects.filter(
                enrollments__student=user,
                enrollments__is_active=True,
                is_active=True,
            ).prefetch_related("enrollments")
        elif user.role == "parent":
            children = FamilyLink.objects.filter(
                parent=user
            ).values_list("student_id", flat=True)
            return Class.objects.filter(
                enrollments__student__in=children,
                enrollments__is_active=True,
                is_active=True,
            ).distinct().prefetch_related("enrollments")
        else:
            # Admin sees all
            return Class.objects.filter(
                is_active=True
            ).prefetch_related("enrollments")


class SessionListView(generics.ListAPIView):
    """List sessions for a specific class."""

    serializer_class = SessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        class_id = self.kwargs.get("class_id")
        return Session.objects.filter(
            class_obj_id=class_id
        ).select_related("class_obj", "class_obj__instructor")


class MyEnrollmentsView(generics.ListAPIView):
    """List the current student's (or parent's children's) enrollments."""

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "student":
            return ClassEnrollment.objects.filter(
                student=user, is_active=True
            ).select_related("class_obj", "class_obj__instructor", "student")
        elif user.role == "parent":
            children = FamilyLink.objects.filter(
                parent=user
            ).values_list("student_id", flat=True)
            return ClassEnrollment.objects.filter(
                student__in=children, is_active=True
            ).select_related("class_obj", "class_obj__instructor", "student")
        elif user.role in ("instructor", "admin"):
            return ClassEnrollment.objects.filter(
                is_active=True
            ).select_related("class_obj", "class_obj__instructor", "student")
        return ClassEnrollment.objects.none()
