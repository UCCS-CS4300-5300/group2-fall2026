import pytest
from django.test import Client
from django.urls import reverse
from django.utils.html import escape

from .models import Character, CharacterEncounter, Encounter, NPC, Quest


pytestmark = pytest.mark.django_db


@pytest.fixture
def npc(encounter):
    return NPC.objects.create(name="Mira", notes="Innkeeper. Knows the old road.", encounter=encounter)


def test_add_npc_and_reload_notes(client, encounter):
    response = client.post(
        reverse("npcs:npc_list", kwargs={"encounter_id": encounter.pk}),
        {"name": "  Mira  ", "notes": "  Innkeeper. Knows the old road.  "},
    )

    assert response.status_code == 201
    npc = NPC.objects.get()
    assert npc.name == "Mira"
    assert npc.notes == "Innkeeper. Knows the old road."

    reloaded = client.get(reverse("npcs:npc_list", kwargs={"encounter_id": encounter.pk}))
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
def test_invalid_npc_is_not_saved(client, data, encounter):
    response = client.post(reverse("npcs:npc_list", kwargs={"encounter_id": encounter.pk}), data)

    assert response.status_code == 400
    assert response.json()
    assert not NPC.objects.exists()


def test_name_and_note_length_limits_and_optional_notes(client, encounter):
    response = client.post(reverse("npcs:npc_list", kwargs={"encounter_id": encounter.pk}), {"name": "n" * 120, "notes": "x" * 1000})
    assert response.status_code == 201
    saved = NPC.objects.get()
    assert saved.name == "n" * 120
    assert saved.notes == "x" * 1000

    response = client.post(reverse("npcs:npc_list", kwargs={"encounter_id": encounter.pk}), {"name": "Town guard"})
    assert response.status_code == 201
    assert NPC.objects.get(name="Town guard").notes == ""


def test_edit_saves_only_the_selected_npc(client, npc, encounter):
    other = NPC.objects.create(name="Town guard", notes="Works at the north gate.", encounter=encounter)
    response = client.post(
        reverse("npcs:npc_detail", args=[npc.pk]),
        {"name": "Mira Stone", "notes": "Now staying in the next town.\nOwes us a favor."},
    )

    assert response.status_code == 200
    npc.refresh_from_db()
    assert npc.name == "Mira Stone"
    assert npc.notes == "Now staying in the next town.\nOwes us a favor."
    other.refresh_from_db()
    assert other.name == "Town guard"
    assert other.notes == "Works at the north gate."
    assert npc.notes.encode() in client.get(reverse("npcs:npc_list", kwargs={"encounter_id": encounter.pk})).content


def test_invalid_edit_keeps_saved_name_and_notes(client, npc):
    response = client.post(
        reverse("npcs:npc_detail", args=[npc.pk]), {"name": " ", "notes": "Changed"}
    )

    assert response.status_code == 400
    assert "name" in response.json()
    npc.refresh_from_db()
    assert npc.name == "Mira"
    assert npc.notes == "Innkeeper. Knows the old road."


def test_delete_removes_only_one_npc(client, npc, encounter):
    other = NPC.objects.create(name="Town guard", encounter=encounter)
    response = client.delete(reverse("npcs:npc_detail", kwargs={"npc_id": npc.pk}))

    assert response.status_code == 204
    assert not NPC.objects.filter(pk=npc.pk).exists()
    assert list(client.get(reverse("npcs:npc_list", kwargs={"encounter_id": encounter.pk})).context["npcs"]) == [other]


def test_missing_npc_and_wrong_methods_do_not_change_records(client, npc):
    missing_url = reverse("npcs:npc_detail", args=[npc.pk + 100])
    assert client.post(missing_url, {"name": "Missing"}).status_code == 404
    assert client.delete(missing_url).status_code == 404
    assert client.delete(reverse("npcs:npc_list", kwargs={"encounter_id": npc.encounter.pk})).status_code == 405
    assert client.get(reverse("npcs:npc_detail", args=[npc.pk])).status_code == 405
    assert NPC.objects.count() == 1


def test_names_and_notes_are_escaped(client, encounter):
    name = '<img src=x onerror="alert(1)">'
    notes = "</textarea><script>alert(1)</script>"
    response = client.post(reverse("npcs:npc_list", kwargs={"encounter_id": encounter.pk}), {"name": name, "notes": notes})

    assert response.status_code == 201
    for page in (response, client.get(reverse("npcs:npc_list", kwargs={"encounter_id": encounter.pk}))):
        for text in (name, notes):
            assert text.encode() not in page.content
            assert escape(text).encode() in page.content


def test_create_edit_and_delete_require_csrf(npc):
    client = Client(enforce_csrf_checks=True)
    collection_url = reverse("npcs:npc_list", kwargs={"encounter_id": npc.encounter.pk})
    detail_url = reverse("npcs:npc_detail", args=[npc.pk])

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
