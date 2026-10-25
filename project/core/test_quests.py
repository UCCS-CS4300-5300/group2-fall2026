import pytest
from django.test import Client
from django.urls import reverse
from django.utils.html import escape

from .models import Character, CharacterEncounter, Encounter, Quest


pytestmark = pytest.mark.django_db


@pytest.fixture
def quest():
    encounter = Encounter.objects.create(name="test_encounter", location="Forest")
    return Quest.objects.create(encounter=encounter, text="Find the missing map")


def test_empty_home_does_not_create_an_encounter(client):
    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert list(response.context["quests"]) == []
    assert not Encounter.objects.exists()
    assert not Quest.objects.exists()


def test_add_quest_trims_text_and_saves_it_on_reload(client):
    response = client.post(
        reverse("core:add_quest"), {"text": "  Find the missing map  "}
    )

    assert response.status_code == 201
    quest = Quest.objects.get()
    assert quest.text == "Find the missing map"
    assert quest.completed is False
    assert quest.encounter.name == "test_encounter"
    assert Encounter.objects.count() == 1
    assert reverse("core:quest_detail", args=[quest.pk]).encode() in response.content
    assert quest.text.encode() in response.content

    home = client.get(reverse("core:home"))
    assert list(home.context["quests"]) == [quest]
    assert quest.text.encode() in home.content


@pytest.mark.parametrize("data", [{}, {"text": ""}, {"text": " \n\t "}, {"text": "x" * 501}])
def test_invalid_quest_does_not_create_partial_records(client, data):
    response = client.post(reverse("core:add_quest"), data)

    assert response.status_code == 400
    assert "text" in response.json()
    assert not Quest.objects.exists()
    assert not Encounter.objects.exists()


def test_maximum_length_quest_reuses_the_current_encounter(client, quest):
    response = client.post(reverse("core:add_quest"), {"text": "x" * 500})

    assert response.status_code == 201
    saved = Quest.objects.get(text="x" * 500)
    assert saved.encounter_id == quest.encounter_id
    assert Encounter.objects.count() == 1
    assert Quest.objects.count() == 2


def test_complete_and_reopen_are_saved_on_reload(client, quest):
    url = reverse("core:quest_detail", args=[quest.pk])
    for completed in (True, False):
        response = client.patch(url, {"completed": completed}, content_type="application/json")

        assert response.status_code == 200
        assert response.json() == {"completed": completed}
        quest.refresh_from_db()
        assert quest.completed is completed
        assert quest.text == "Find the missing map"
        home = client.get(reverse("core:home"))
        assert home.context["quests"].get(pk=quest.pk).completed is completed
        assert (b"text-decoration-line-through" in home.content) is completed


@pytest.mark.parametrize(
    "payload",
    ["not json", "null", "[]", "{}", '{"completed": 1}', '{"completed": "false"}', '{"completed": null}'],
)
def test_invalid_completion_leaves_quest_unchanged(client, quest, payload):
    quest.completed = True
    quest.save()
    response = client.patch(
        reverse("core:quest_detail", args=[quest.pk]), payload, content_type="application/json"
    )

    assert response.status_code == 400
    assert "error" in response.json()
    quest.refresh_from_db()
    assert quest.completed is True
    assert quest.text == "Find the missing map"


def test_delete_removes_only_the_selected_quest(client, quest):
    other = Quest.objects.create(encounter=quest.encounter, text="Return to town")
    response = client.delete(reverse("core:quest_detail", args=[quest.pk]))

    assert response.status_code == 204
    assert response.content == b""
    assert not Quest.objects.filter(pk=quest.pk).exists()
    assert Quest.objects.get(pk=other.pk).text == "Return to town"
    home = client.get(reverse("core:home"))
    assert list(home.context["quests"]) == [other]
    assert b"Find the missing map" not in home.content
    assert Encounter.objects.filter(pk=other.encounter_id).exists()


def test_missing_and_other_encounter_quests_cannot_be_changed(client, quest):
    other_encounter = Encounter.objects.create(name="Cave", location="Mountain")
    other = Quest.objects.create(encounter=other_encounter, text="Explore the cave")

    home = client.get(reverse("core:home"))
    assert list(home.context["quests"]) == [quest]
    assert other.text.encode() not in home.content
    for quest_id in (other.pk, other.pk + 1000):
        url = reverse("core:quest_detail", args=[quest_id])
        response = client.patch(url, {"completed": True}, content_type="application/json")
        assert response.status_code == 404
        assert client.delete(url).status_code == 404

    other.refresh_from_db()
    quest.refresh_from_db()
    assert other.completed is False
    assert quest.completed is False
    assert Quest.objects.count() == 2


def test_quest_endpoints_reject_wrong_methods(client, quest):
    add_url = reverse("core:add_quest")
    detail_url = reverse("core:quest_detail", args=[quest.pk])
    for method in ("GET", "PATCH", "DELETE"):
        assert client.generic(method, add_url).status_code == 405
    for method in ("GET", "POST", "PUT"):
        assert client.generic(method, detail_url).status_code == 405

    quest.refresh_from_db()
    assert quest.completed is False
    assert Quest.objects.count() == 1


def test_quest_text_is_escaped_in_fragment_and_page(client):
    text = '<img src=x onerror="alert(1)">'
    response = client.post(reverse("core:add_quest"), {"text": text})
    assert response.status_code == 201
    assert Quest.objects.get().text == text

    home = client.get(reverse("core:home"))
    for content in (response.content, home.content):
        assert text.encode() not in content
        assert escape(text).encode() in content


def test_adding_completing_and_deleting_require_csrf():
    client = Client(enforce_csrf_checks=True)
    add_url = reverse("core:add_quest")
    data = {"text": "Return the map"}
    assert client.post(add_url, data).status_code == 403
    assert not Quest.objects.exists()

    home = client.get(reverse("core:home"))
    quest_form = home.content.decode().split('id="questForm"', 1)[1].split("</form>", 1)[0]
    assert 'name="csrfmiddlewaretoken"' in quest_form
    token = client.cookies["csrftoken"].value
    response = client.post(add_url, {**data, "csrfmiddlewaretoken": token})
    assert response.status_code == 201

    quest = Quest.objects.get()
    url = reverse("core:quest_detail", args=[quest.pk])
    assert client.patch(url, {"completed": True}, content_type="application/json").status_code == 403
    quest.refresh_from_db()
    assert quest.completed is False
    response = client.patch(
        url, {"completed": True}, content_type="application/json", HTTP_X_CSRFTOKEN=token
    )
    assert response.status_code == 200
    quest.refresh_from_db()
    assert quest.completed is True
    assert client.delete(url).status_code == 403
    assert Quest.objects.filter(pk=quest.pk).exists()
    assert client.delete(url, HTTP_X_CSRFTOKEN=token).status_code == 204
    assert not Quest.objects.exists()


def test_quest_changes_leave_combatants_alone(client):
    encounter = Encounter.objects.create(name="test_encounter", location="Forest")
    character = Character.objects.create(name="Goblin", max_hp=12, armor_class=13)
    entry = CharacterEncounter.objects.create(
        encounter=encounter, character=character, remaining_hp=8,
        initiative=14, x_pos=80, y_pos=100,
    )
    assert client.post(reverse("core:add_quest"), {"text": "Find the camp"}).status_code == 201
    quest = Quest.objects.get()
    assert quest.encounter_id == encounter.pk
    url = reverse("core:quest_detail", args=[quest.pk])
    assert client.patch(url, {"completed": True}, content_type="application/json").status_code == 200
    assert client.delete(url).status_code == 204

    entry.refresh_from_db()
    character.refresh_from_db()
    assert (entry.remaining_hp, entry.initiative, entry.x_pos, entry.y_pos) == (8, 14, 80, 100)
    assert (character.name, character.max_hp, character.armor_class) == ("Goblin", 12, 13)
    assert CharacterEncounter.objects.count() == Character.objects.count() == Encounter.objects.count() == 1
