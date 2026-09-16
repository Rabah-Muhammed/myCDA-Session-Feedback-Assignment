from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for the CDA unified backend.

    Every user has exactly one `role` that determines what they can
    see and do across the platform.
    """

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        INSTRUCTOR = "instructor", "Instructor"
        PARENT = "parent", "Parent"
        STUDENT = "student", "Student"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )
    preferred_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_display_name(self):
        """Return preferred name, full name, or email -- in that order."""
        if self.preferred_name:
            return self.preferred_name
        full = self.get_full_name()
        return full if full else self.email

    def __str__(self):
        return f"{self.get_display_name()} ({self.role})"


class FamilyLink(models.Model):
    """
    Links a parent to a student. A parent can have multiple linked
    students. A student can have multiple linked parents.

    This is used to determine which students a parent can act on
    behalf of (e.g., submitting feedback, viewing schedules).
    """

    parent = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="family_children",
        limit_choices_to={"role": "parent"},
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="family_parents",
        limit_choices_to={"role": "student"},
    )
    relationship = models.CharField(
        max_length=50,
        default="parent",
        help_text="e.g., parent, guardian, grandparent",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("parent", "student")
        verbose_name = "family link"
        verbose_name_plural = "family links"

    def __str__(self):
        return f"{self.parent.get_display_name()} -> {self.student.get_display_name()}"
