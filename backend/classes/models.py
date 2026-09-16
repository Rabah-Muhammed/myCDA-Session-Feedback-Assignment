from django.db import models
from accounts.models import User


class Class(models.Model):
    """A recurring class (e.g., 'Lincoln-Douglas Debate Fundamentals')."""

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    instructor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="taught_classes",
        limit_choices_to={"role": "instructor"},
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    class Meta:
        verbose_name_plural = "classes"

    def __str__(self):
        return self.name


class ClassEnrollment(models.Model):
    """Tracks which students are enrolled in which classes."""

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="enrollments",
        limit_choices_to={"role": "student"},
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("class_obj", "student")

    def __str__(self):
        return f"{self.student} in {self.class_obj}"


class Session(models.Model):
    """
    A single occurrence of a class (e.g., the Tuesday Jan 14 session of
    'Lincoln-Douglas Debate Fundamentals').

    The `session_metadata` JSONField stores variable session-level data.
    Current schema:
    {
        "duration_minutes": <int>,
        "topic_covered": <str>,
        "location": <str, optional>,
        "notes": <str, optional>
    }
    """

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    class_obj = models.ForeignKey(
        Class,
        on_delete=models.CASCADE,
        related_name="sessions",
    )
    scheduled_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )
    session_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Variable session data. See model docstring for schema.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-scheduled_date"]

    def __str__(self):
        return (
            f"{self.class_obj.name} - "
            f"{self.scheduled_date.strftime('%Y-%m-%d')} "
            f"({self.status})"
        )

    @property
    def duration_minutes(self):
        """Convenience accessor for the duration in session_metadata."""
        return self.session_metadata.get("duration_minutes", 60)

    @property
    def topic(self):
        """Convenience accessor for the topic in session_metadata."""
        return self.session_metadata.get("topic_covered", "")
