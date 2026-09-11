import pytest
from django.urls import reverse

from sessions.models import StudySession


@pytest.mark.django_db
def test_session_list_page_displays_saved_session(client):
    StudySession.objects.create(topic="Coverage", duration_minutes=45)
    response = client.get(reverse("session-list"))
    assert response.status_code == 200
    assert b"Coverage" in response.content
    assert b"45" in response.content
