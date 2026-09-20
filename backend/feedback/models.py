from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from accounts.models import User
from classes.models import Session


class SessionFeedback(models.Model):
    """
    Captures structured feedback for a completed class session.
    Submitted either by the student directly or by a linked parent on their behalf.
    """

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="feedbacks",
        help_text="The completed class session being reviewed.",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="student_feedbacks",
        limit_choices_to={"role": "student"},
        help_text="The student whose experience this feedback represents.",
    )
    submitter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submitted_feedbacks",
        help_text="The user who submitted this review (student or parent).",
    )
    rating_clarity = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Clarity of concepts explained (1-5).",
    )
    rating_engagement = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="How engaging the session was (1-5).",
    )
    rating_pace = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Pacing of the class (1-5).",
    )
    notes = models.TextField(
        max_length=500,
        blank=True,
        help_text="Optional comments or suggestions (max 500 characters).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("session", "student")
        ordering = ["-created_at"]
        verbose_name = "session feedback"
        verbose_name_plural = "session feedbacks"

    @property
    def created_by(self):
        """Bridge property so BaseModelSerializer can read the author."""
        return self.submitter

    def __str__(self):
        return f"Feedback: {self.student.get_display_name()} for {self.session}"