import pytest
from django.core.exceptions import ValidationError

from sessions.models import StudySession


@pytest.mark.django_db
def test_session_stores_topic_and_duration():
    session = StudySession.objects.create(topic="Mutation Testing", duration_minutes=60)
    saved = StudySession.objects.get(pk=session.pk)
    assert saved.topic == "Mutation Testing"
    assert saved.duration_minutes == 60


# HW1 Part 4:
# Add a test showing that StudySession correctly stores the new "subject"
# information that you add in Part 3.


# HW1 Part 4:
# Add a test showing that a negative duration is rejected.
# Beginner hint:
# - construct a StudySession with a negative duration
# - call full_clean()
# - pytest.raises(ValidationError) may be useful
