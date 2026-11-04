import pytest
from django.urls import reverse

from .models import Character, CharacterEncounter, Encounter


pytestmark = pytest.mark.django_db

@pytest.fixture
def combatant_player(combatant):
    c = combatant
    c.char_type="player"
    return c

@pytest.fixture
def combatant_enemy(combatant):
    c = combatant
    c.char_type="enemy"
    return c

def test_add_combatant_saves_character_and_card_on_reload(client, encounter):
    response = client.post(
        reverse("core:add_combatant", kwargs={"encounter_id": encounter.pk}),
        {"name": "Goblin", "max_hp": 12, "armor_class": 13},
    )

    assert response.status_code == 200
    assert Character.objects.count() == 1
    entry = CharacterEncounter.objects.select_related("character").get()
    assert entry.character.name == "Goblin"
    assert entry.character.max_hp == 12
    assert entry.character.armor_class == 13
    assert (
        entry.character.strength_save_bonus,
        entry.character.dexterity_save_bonus,
        entry.character.constitution_save_bonus,
        entry.character.intelligence_save_bonus,
        entry.character.wisdom_save_bonus,
        entry.character.charisma_save_bonus,
    ) == (0, 0, 0, 0, 0, 0)
    assert entry.remaining_hp == 12
    assert entry.initiative == 0
    assert entry.x_pos == CharacterEncounter.DEFAULT_X
    assert entry.y_pos == CharacterEncounter.DEFAULT_Y
    assert f'data-id="{entry.pk}"'.encode() in response.content

    encounter_page = client.get(reverse("core:encounter", kwargs={"encounter_id": encounter.pk}))
    assert encounter_page.status_code == 200
    assert b"Goblin" in encounter_page.content
    assert f'data-id="{entry.pk}"'.encode() in encounter_page.content
    assert list(encounter_page.context["items"]) == [entry]


def test_add_combatant_saves_and_displays_saving_throw_bonuses(client, encounter):
    response = client.post(
        reverse("core:add_combatant", kwargs={"encounter_id": encounter.pk}),
        {
            "name": "Ayla",
            "max_hp": 20,
            "armor_class": 15,
            "char_type": "player",
            "strength_save_bonus": 2,
            "dexterity_save_bonus": -1,
            "constitution_save_bonus": 0,
            "intelligence_save_bonus": 3,
            "wisdom_save_bonus": 1,
            "charisma_save_bonus": 4,
        },
    )

    assert response.status_code == 200
    entry = CharacterEncounter.objects.select_related("character").get()
    assert entry.character.char_type == "player"
    assert (
        entry.character.strength_save_bonus,
        entry.character.dexterity_save_bonus,
        entry.character.constitution_save_bonus,
        entry.character.intelligence_save_bonus,
        entry.character.wisdom_save_bonus,
        entry.character.charisma_save_bonus,
    ) == (2, -1, 0, 3, 1, 4)
    assert b"STR <strong>2</strong>" in response.content
    assert b"DEX <strong>-1</strong>" in response.content

    encounter_page = client.get(reverse("core:encounter", kwargs={"encounter_id": encounter.pk}))
    assert encounter_page.status_code == 200
    assert b"CHA <strong>4</strong>" in encounter_page.content


def test_home_add_combatant_form_includes_saving_throw_bonuses(client, encounter):
    response = client.get(reverse("core:encounter", kwargs={"encounter_id": encounter.pk}))

    assert response.status_code == 200
    for field in (
        "strength_save_bonus",
        "dexterity_save_bonus",
        "constitution_save_bonus",
        "intelligence_save_bonus",
        "wisdom_save_bonus",
        "charisma_save_bonus",
    ):
        assert f'name="{field}"'.encode() in response.content


@pytest.mark.parametrize(
    "data, field",
    [
        ({"max_hp": 12, "armor_class": 13}, "name"),
        ({"name": "Goblin", "max_hp": "many", "armor_class": 13}, "max_hp"),
        ({"name": "Goblin", "max_hp": 12, "armor_class": "tough"}, "armor_class"),
        (
            {
                "name": "Goblin",
                "max_hp": 12,
                "armor_class": 13,
                "constitution_save_bonus": "strong",
            },
            "constitution_save_bonus",
        ),
    ],
)
def test_invalid_combatant_does_not_create_partial_records(client, data, field, encounter):
    response = client.post(reverse("core:add_combatant", kwargs={"encounter_id": encounter.pk}), data)

    assert response.status_code == 400
    assert field in response.json()
    assert not Character.objects.exists()
    assert not CharacterEncounter.objects.exists()


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
    encounter_page = client.get(reverse("core:encounter", kwargs={"encounter_id": combatant.encounter.pk}))
    assert b"left: 175px; top: 220px;" in encounter_page.content


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
    assert client.get(reverse("core:add_combatant", kwargs={"encounter_id": combatant.encounter.pk})).status_code == 405
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

@pytest.mark.django_db
def test_default_enemy_type(combatant):
    assert combatant.character.char_type=='enemy'

@pytest.mark.django_db
def test_add_combatant_sets_type(client, encounter):
    char_form = {
        "name": "test",
        "max_hp": 12,
        "armor_class": 20,
        "char_type": "player",
    }

    res = client.post(reverse("core:add_combatant", kwargs={"encounter_id": encounter.pk}), char_form)
    
    assert res.status_code == 200 # Request went through
    assert Character.objects.filter(name="test").exists() # Character was created
    assert Character.objects.get(name="test").char_type == "player"

def test_empty_encounter_does_not_create_an_encounter(client):
    response = client.get(reverse("core:encounter", kwargs={"encounter_id": 999}))

    assert response.status_code == 404 # No encounter exists, this should 404
    assert not Encounter.objects.exists()

@pytest.mark.parametrize(
    "payload",
    [
        {"name": "valid", "location": "candyland", "description": "funny"},
        {"name": "x" * 120, "location": "candyland", "description": "funny"},
    ],
)
def test_add_valid_encounter_creates_new_encounter(client, payload):
    print(payload)
    response = client.post(reverse("core:add_encounter"), payload)
    assert response.status_code == 200 # Successful
    assert Encounter.objects.exists() # Encounter was added

def test_add_valid_encounter_shows_on_dashboard(client):
    payload = {"name": "valid", "location": "candyland", "description": "funny"}
    response = client.post(reverse("core:add_encounter"), payload)
    assert response.status_code == 200 # Successful
    assert Encounter.objects.exists() # Encounter was added

    # Get dashboard
    dash_res = client.get(reverse("core:dashboard"))
    assert dash_res.status_code == 200 # Successful
    assert b"valid" in dash_res.content
    assert b"candyland" in dash_res.content
    assert b"funny" in dash_res.content

@pytest.mark.parametrize(
    "payload",
    [
        {"name": "", "location": "candyland", "description": "funny"},
        {"name": "x"*121, "location": "candyland", "description": "funny"},
    ],
)
def test_add_invalid_encounter_name_rejected(client, payload):
    response = client.post(reverse("core:add_encounter"), payload)
    assert response.status_code == 400 # Unsuccessful
    assert not Encounter.objects.exists() # Encounter was not added

@pytest.mark.parametrize(
    "payload",
    [
        {"name": "valid", "location": "x" * 121, "description": "funny"},
        {"name": "valid", "location": "x", "description": "x" * 256},
    ],
)
def test_add_invalid_encounter_location_description_length_rejected(client, payload):
    response = client.post(reverse("core:add_encounter"), payload)
    assert response.status_code == 400 # Unsuccessful
    assert not Encounter.objects.exists() # Encounter was not added

@pytest.mark.parametrize(
    "payload",
    [
        {"name": "valid", "location": "x" * 120, "description": "funny"},
        {"name": "valid", "location": "x", "description": "x" * 255},
        {"name": "valid", "location": "x", "description": ""},
        {"name": "valid", "location": "", "description": "x"},
    ],
)
def test_add_valid_encounter_location_description_length_accepted(client, payload):
    response = client.post(reverse("core:add_encounter"), payload)
    assert response.status_code == 200 # Successful
    assert Encounter.objects.exists() # Encounter was added