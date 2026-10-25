from html.parser import HTMLParser

import pytest
from django.test import Client
from django.urls import reverse

from .models import CharacterEncounter


class PageForms(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.forms = {}
        self.current = None
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.current = []
            form_id = attrs.get("id")
            if form_id is not None:
                self.forms[form_id] = self.current
        if self.current is not None:
            self.current.append((tag, attrs))

    def handle_endtag(self, tag):
        if tag == "form":
            self.current = None


@pytest.mark.django_db
def test_home_has_dice_choices_and_count_limits(client):
    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    form = PageForms(response.content.decode()).forms["diceForm"]
    options = [attrs for tag, attrs in form if tag == "option"]
    assert [option["value"] for option in options] == ["4", "6", "8", "10", "12", "20"]
    assert [option["value"] for option in options if "selected" in option] == ["20"]
    count = next(attrs for tag, attrs in form if attrs.get("name") == "count")
    assert count["type"] == "number"
    assert count["value"] == count["min"] == count["step"] == "1"
    assert count["max"] == "20"
    assert "required" in count
    ids = {attrs.get("id") for tag, attrs in form}
    assert {"id_sides", "id_count", "diceResult", "diceError"} <= ids


@pytest.mark.django_db
def test_combatant_changes_still_require_the_token_from_the_page():
    client = Client(enforce_csrf_checks=True)
    add_url = reverse("core:add_combatant")
    data = {"name": "Goblin", "max_hp": 12, "armor_class": 13}

    assert client.post(add_url, data).status_code == 403
    response = client.get(reverse("core:home"))
    form = PageForms(response.content.decode()).forms["addForm"]
    token = next(attrs["value"] for tag, attrs in form if attrs.get("name") == "csrfmiddlewaretoken")
    response = client.post(add_url, {**data, "csrfmiddlewaretoken": token})
    assert response.status_code == 200

    entry = CharacterEncounter.objects.get()
    move_url = reverse("core:move_combatant", args=[entry.pk])
    position = {"x": 120, "y": 160}
    assert client.patch(move_url, position, content_type="application/json").status_code == 403
    response = client.patch(
        move_url, position, content_type="application/json", HTTP_X_CSRFTOKEN=token
    )
    assert response.status_code == 200
    entry.refresh_from_db()
    assert (entry.x_pos, entry.y_pos) == (120, 160)
