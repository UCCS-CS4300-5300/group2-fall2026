from django.core.exceptions import ValidationError
from django.db import models


class StudySession(models.Model):
    """A single study session. HW1 Part 3 asks students to add a subject field."""

    topic = models.CharField(max_length=150)
    duration_minutes = models.IntegerField()
    completed_on = models.DateField(auto_now_add=True)

    def clean(self):
        """HW1 Part 4: add validation so negative duration is rejected."""
        # TODO (HW1 Part 4): add validation for negative duration.
        pass

    def __str__(self):
        return f"{self.topic} ({self.duration_minutes} min)"
