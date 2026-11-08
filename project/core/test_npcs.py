import pytest
from django.test import Client
from django.urls import reverse
from django.utils.html import escape

from .models import Character, CharacterEncounter, Encounter, NPC, Quest


pytestmark = pytest.mark.django_db


@pytest.fixture
def npc():
    return NPC.objects.create(name="Mira", notes="Innkeeper. Knows the old road.")


def test_add_npc_and_reload_notes(client):
    response = client.post(
        reverse("npcs:list"),
        {"name": "  Mira  ", "notes": "  Innkeeper. Knows the old road.  "},
    )

    assert response.status_code == 201
    npc = NPC.objects.get()
    assert npc.name == "Mira"
    assert npc.notes == "Innkeeper. Knows the old road."
    assert not Character.objects.exists()
    assert not Encounter.objects.exists()

    reloaded = client.get(reverse("npcs:list"))
    assert reloaded.status_code == 200
    assert list(reloaded.context["npcs"]) == [npc]
    assert npc.name.encode() in reloaded.content
    assert npc.notes.encode() in reloaded.content


@pytest.mark.parametrize("data", [
    {},
    {"name": " \n\t ", "notes": "No name"},
    {"name": "x" * 121},
    {"name": "Mira", "notes": "x" * 1001},
])
def test_invalid_npc_is_not_saved(client, data):
    response = client.post(reverse("npcs:list"), data)

    assert response.status_code == 400
    assert response.json()
    assert not NPC.objects.exists()


def test_name_and_note_length_limits_and_optional_notes(client):
    response = client.post(reverse("npcs:list"), {"name": "n" * 120, "notes": "x" * 1000})
    assert response.status_code == 201
    saved = NPC.objects.get()
    assert saved.name == "n" * 120
    assert saved.notes == "x" * 1000

    response = client.post(reverse("npcs:list"), {"name": "Town guard"})
    assert response.status_code == 201
    assert NPC.objects.get(name="Town guard").notes == ""


def test_edit_saves_only_the_selected_npc(client, npc):
    other = NPC.objects.create(name="Town guard", notes="Works at the north gate.")
    response = client.post(
        reverse("npcs:detail", args=[npc.pk]),
        {"name": "Mira Stone", "notes": "Now staying in the next town.\nOwes us a favor."},
    )

    assert response.status_code == 200
    npc.refresh_from_db()
    assert npc.name == "Mira Stone"
    assert npc.notes == "Now staying in the next town.\nOwes us a favor."
    other.refresh_from_db()
    assert other.name == "Town guard"
    assert other.notes == "Works at the north gate."
    assert npc.notes.encode() in client.get(reverse("npcs:list")).content


def test_invalid_edit_keeps_saved_name_and_notes(client, npc):
    response = client.post(
        reverse("npcs:detail", args=[npc.pk]), {"name": " ", "notes": "Changed"}
    )

    assert response.status_code == 400
    assert "name" in response.json()
    npc.refresh_from_db()
    assert npc.name == "Mira"
    assert npc.notes == "Innkeeper. Knows the old road."


def test_npcs_stay_available_after_an_encounter_is_deleted(client, npc):
    first = Encounter.objects.create(name="Forest", location="Woods")
    second = Encounter.objects.create(name="Town", location="Inn")
    character = Character.objects.create(name="Fighter", max_hp=20)
    entry = CharacterEncounter.objects.create(
        encounter=second, character=character, remaining_hp=12
    )
    quest = Quest.objects.create(encounter=second, text="Find the map")

    first.delete()
    response = client.get(reverse("npcs:list"))
    assert list(response.context["npcs"]) == [npc]
    assert npc.notes.encode() in response.content
    client.post(reverse("npcs:detail", args=[npc.pk]), {"name": "Mira", "notes": "Met again in town."})
    npc.refresh_from_db()
    assert npc.notes == "Met again in town."
    entry.refresh_from_db()
    quest.refresh_from_db()
    assert entry.remaining_hp == 12
    assert quest.text == "Find the map"
    assert quest.completed is False


def test_delete_removes_only_one_npc(client, npc):
    other = NPC.objects.create(name="Town guard")
    response = client.delete(reverse("npcs:detail", args=[npc.pk]))

    assert response.status_code == 204
    assert not NPC.objects.filter(pk=npc.pk).exists()
    assert list(client.get(reverse("npcs:list")).context["npcs"]) == [other]


def test_missing_npc_and_wrong_methods_do_not_change_records(client, npc):
    missing_url = reverse("npcs:detail", args=[npc.pk + 100])
    assert client.post(missing_url, {"name": "Missing"}).status_code == 404
    assert client.delete(missing_url).status_code == 404
    assert client.delete(reverse("npcs:list")).status_code == 405
    assert client.get(reverse("npcs:detail", args=[npc.pk])).status_code == 405
    assert NPC.objects.count() == 1


def test_names_and_notes_are_escaped(client):
    name = '<img src=x onerror="alert(1)">'
    notes = "</textarea><script>alert(1)</script>"
    response = client.post(reverse("npcs:list"), {"name": name, "notes": notes})

    assert response.status_code == 201
    for page in (response, client.get(reverse("npcs:list"))):
        for text in (name, notes):
            assert text.encode() not in page.content
            assert escape(text).encode() in page.content


def test_create_edit_and_delete_require_csrf(npc):
    client = Client(enforce_csrf_checks=True)
    collection_url = reverse("npcs:list")
    detail_url = reverse("npcs:detail", args=[npc.pk])

    assert client.post(collection_url, {"name": "Guard"}).status_code == 403
    assert client.post(detail_url, {"name": "Changed"}).status_code == 403
    assert client.delete(detail_url).status_code == 403
    npc.refresh_from_db()
    assert npc.name == "Mira"
    assert NPC.objects.count() == 1

    client.get(collection_url)
    token = client.cookies["csrftoken"].value
    assert client.post(collection_url, {"name": "Guard"}, HTTP_X_CSRFTOKEN=token).status_code == 201
    assert client.post(detail_url, {"name": "Mira Stone"}, HTTP_X_CSRFTOKEN=token).status_code == 200
    npc.refresh_from_db()
    assert npc.name == "Mira Stone"
    assert client.delete(detail_url, HTTP_X_CSRFTOKEN=token).status_code == 204
    assert not NPC.objects.filter(pk=npc.pk).exists()
