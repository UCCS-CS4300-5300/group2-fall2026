import pytest
from django.test import Client
from django.urls import reverse

from .models import Character, Encounter, EncounterCombatant

@pytest.mark.django_db
def test_character_get_modifier():
    char=Character(strength=8)
    assert Character.get_modifier(char.strength) == -1


@pytest.mark.django_db
def test_home_shows_encounter_creation_form():
    response = Client().get(reverse("core:home"))

    assert response.status_code == 200
    assert "form" in response.context
    assert "No encounters yet" in response.content.decode()


@pytest.mark.django_db
def test_home_creates_and_lists_encounter(client):
    response = client.post(
        reverse("core:home"),
        {"name": "Goblin ambush", "notes": "Three goblins near the bridge."},
    )

    assert response.status_code == 302
    encounter = Encounter.objects.get(name="Goblin ambush")
    assert encounter.notes == "Three goblins near the bridge."

    response = client.get(reverse("core:home"))
    assert "Goblin ambush" in response.content.decode()
    assert "Three goblins near the bridge." in response.content.decode()
    assert reverse("core:encounter_detail", args=[encounter.id]) in response.content.decode()


@pytest.mark.django_db
def test_home_rejects_encounter_without_name(client):
    response = client.post(reverse("core:home"), {"name": "", "notes": "Missing a title"})

    assert response.status_code == 200
    assert Encounter.objects.count() == 0
    assert response.context["form"].errors["name"]


@pytest.mark.django_db
def test_encounter_workspace_adds_combatant(client):
    encounter = Encounter.objects.create(name="Ruined watchtower")

    response = client.post(
        reverse("core:encounter_detail", args=[encounter.id]),
        {
            "name": "Goblin scout",
            "role": "enemy",
            "hit_points": 7,
            "armor_class": 15,
            "attack_bonus": 4,
            "damage": "1d6+2",
        },
    )

    assert response.status_code == 302
    combatant = EncounterCombatant.objects.get(encounter=encounter)
    assert combatant.name == "Goblin scout"
    assert combatant.hit_points == 7
    assert combatant.damage == "1d6+2"

    response = client.get(reverse("core:encounter_detail", args=[encounter.id]))
    page = response.content.decode()
    assert "Goblin scout" in page
    assert "1d6+2" in page
    assert "Combat log" in page


@pytest.mark.django_db
def test_csrf_accepts_forwarded_local_https_origin():
    client = Client(enforce_csrf_checks=True)
    response = client.get(
        reverse("core:home"),
        secure=True,
        HTTP_HOST="localhost:8000",
    )
    csrf_token = client.cookies["csrftoken"].value

    response = client.post(
        reverse("core:home"),
        {"name": "Crypt entrance", "notes": "", "csrfmiddlewaretoken": csrf_token},
        secure=True,
        HTTP_HOST="localhost:8000",
        HTTP_ORIGIN="https://localhost:8000",
    )

    assert response.status_code == 302
    assert Encounter.objects.filter(name="Crypt entrance").exists()


@pytest.mark.django_db
def test_csrf_rejects_untrusted_origin():
    client = Client(enforce_csrf_checks=True)
    client.get(reverse("core:home"))
    csrf_token = client.cookies["csrftoken"].value

    response = client.post(
        reverse("core:home"),
        {"name": "Should not save", "notes": "", "csrfmiddlewaretoken": csrf_token},
        HTTP_ORIGIN="https://attacker.example",
    )

    assert response.status_code == 403
    assert not Encounter.objects.filter(name="Should not save").exists()