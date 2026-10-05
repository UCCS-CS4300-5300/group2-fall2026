import pytest
from django.urls import reverse

from .models import Character, CharacterEncounter, Encounter


pytestmark = pytest.mark.django_db


@pytest.fixture
def combatant():
    character = Character.objects.create(name="Goblin", max_hp=12, armor_class=13)
    encounter = Encounter.objects.create(name="Forest", location="Trail")
    return CharacterEncounter.objects.create(
        character=character,
        encounter=encounter,
        remaining_hp=12,
        x_pos=50,
        y_pos=60,
    )


def test_add_combatant_saves_character_and_card_on_reload(client):
    response = client.post(
        reverse("core:add_combatant"),
        {"name": "Goblin", "max_hp": 12, "armor_class": 13},
    )

    assert response.status_code == 200
    assert Character.objects.count() == 1
    assert Encounter.objects.count() == 1
    entry = CharacterEncounter.objects.select_related("character").get()
    assert entry.character.name == "Goblin"
    assert entry.character.max_hp == 12
    assert entry.character.armor_class == 13
    assert entry.remaining_hp == 12
    assert entry.initiative == 0
    assert entry.x_pos == CharacterEncounter.DEFAULT_X
    assert entry.y_pos == CharacterEncounter.DEFAULT_Y
    assert f'data-id="{entry.pk}"'.encode() in response.content

    home = client.get(reverse("core:home"))
    assert home.status_code == 200
    assert b"Goblin" in home.content
    assert f'data-id="{entry.pk}"'.encode() in home.content
    assert list(home.context["items"]) == [entry]


@pytest.mark.parametrize(
    "data, field",
    [
        ({"max_hp": 12, "armor_class": 13}, "name"),
        ({"name": "Goblin", "max_hp": "many", "armor_class": 13}, "max_hp"),
        ({"name": "Goblin", "max_hp": 12, "armor_class": "tough"}, "armor_class"),
    ],
)
def test_invalid_combatant_does_not_create_partial_records(client, data, field):
    response = client.post(reverse("core:add_combatant"), data)

    assert response.status_code == 400
    assert field in response.json()
    assert not Character.objects.exists()
    assert not CharacterEncounter.objects.exists()
    assert not Encounter.objects.exists()


def test_move_combatant_persists_position_after_reload(client, combatant):
    response = client.patch(
        reverse("core:move_combatant", args=[combatant.pk]),
        {"x": 175, "y": 220},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {"x": 175, "y": 220}
    combatant.refresh_from_db()
    assert (combatant.x_pos, combatant.y_pos) == (175, 220)
    home = client.get(reverse("core:home"))
    assert b"left: 175px; top: 220px;" in home.content


@pytest.mark.parametrize(
    "payload",
    ["not json", "{}", '{"x": 10}', '{"x": "bad", "y": 10}', '{"x": null, "y": 10}'],
)
def test_invalid_move_leaves_saved_position_unchanged(client, combatant, payload):
    response = client.patch(
        reverse("core:move_combatant", args=[combatant.pk]),
        payload,
        content_type="application/json",
    )

    assert response.status_code == 400
    combatant.refresh_from_db()
    assert (combatant.x_pos, combatant.y_pos) == (50, 60)


def test_move_missing_combatant_returns_404(client):
    response = client.patch(
        reverse("core:move_combatant", args=[999]),
        {"x": 10, "y": 20},
        content_type="application/json",
    )

    assert response.status_code == 404


def test_combatant_endpoints_reject_wrong_methods(client, combatant):
    assert client.get(reverse("core:add_combatant")).status_code == 405
    response = client.post(
        reverse("core:move_combatant", args=[combatant.pk]), {"x": 10, "y": 20}
    )
    assert response.status_code == 405
    combatant.refresh_from_db()
    assert (combatant.x_pos, combatant.y_pos) == (50, 60)


def test_same_character_has_separate_state_in_each_encounter(combatant):
    other_encounter = Encounter.objects.create(name="Cave", location="Entrance")
    other_entry = CharacterEncounter.objects.create(
        character=combatant.character,
        encounter=other_encounter,
        remaining_hp=12,
        initiative=2,
        x_pos=70,
        y_pos=80,
    )

    combatant.remaining_hp = 3
    combatant.initiative = 18
    combatant.x_pos = 100
    combatant.y_pos = 120
    combatant.save()

    combatant.refresh_from_db()
    other_entry.refresh_from_db()
    combatant.character.refresh_from_db()
    assert (combatant.remaining_hp, combatant.initiative) == (3, 18)
    assert (other_entry.remaining_hp, other_entry.initiative) == (12, 2)
    assert (other_entry.x_pos, other_entry.y_pos) == (70, 80)
    assert combatant.character.max_hp == 12
