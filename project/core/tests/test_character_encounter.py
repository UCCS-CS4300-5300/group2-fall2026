import pytest
import json

from django.urls import reverse


# Tests for updating character HP
@pytest.mark.django_db
def test_character_hp_endpoint_valid_int_success(client, combatant):
    c = combatant
    res = client.patch(reverse('core:update_hp', args=[c.pk]), {"remaining_hp": 9}, content_type="application/json")
    assert res.status_code == 200 # Response returned
    assert res.json()["remaining_hp"] == 9 # Response is accurate

    c.refresh_from_db() # Get update
    assert c.remaining_hp == 9 # Database was updated

@pytest.mark.django_db
def test_character_hp_endpoint_invalid_key(client, combatant):
    res = client.patch(reverse('core:update_hp', args=[combatant.pk]), {"invalid": 19}, content_type="application/json")
    assert res.status_code == 400 # Response returned

@pytest.mark.django_db
def test_character_hp_endpoint_float_hp_rejected(client, combatant):
    res = client.patch(reverse('core:update_hp', args=[combatant.pk]), {"remaining_hp": 10.9}, content_type="application/json")
    assert res.status_code == 400 # Response returned

@pytest.mark.django_db
def test_character_hp_endpoint_float_hp_accepted(client, combatant):
    res = client.patch(reverse('core:update_hp', args=[combatant.pk]), {"remaining_hp": 10.0}, content_type="application/json")
    assert res.status_code == 200 # Response returned

@pytest.mark.django_db
def test_character_hp_endpoint_string_hp_rejected(client, combatant):
    res = client.patch(reverse('core:update_hp', args=[combatant.pk]), {"remaining_hp": "10"}, content_type="application/json")
    assert res.status_code == 400 # Response returned

@pytest.mark.django_db
def test_character_hp_too_large_returns_max(client, combatant):
    res = client.patch(reverse('core:update_hp', args=[combatant.pk]), {"remaining_hp": 100}, content_type="application/json")
    assert res.status_code == 200 # Response returned
    assert res.json()["remaining_hp"] == 12

    combatant.refresh_from_db()
    assert combatant.remaining_hp == 12

# Tests for updating character initiative
@pytest.mark.django_db
def test_character_initiative_endpoint_valid_int_success(client, combatant):
    c = combatant
    res = client.patch(reverse('core:update_initiative', args=[c.pk]), {"initiative": 9}, content_type="application/json")
    assert res.status_code == 200 # Response returned
    assert res.json()["initiative"] == 9 # Response is accurate

    c.refresh_from_db() # Get update
    assert c.initiative == 9 # Database was updated

@pytest.mark.django_db
def test_character_initiative_endpoint_invalid_key(client, combatant):
    res = client.patch(reverse('core:update_initiative', args=[combatant.pk]), {"invalid": 19}, content_type="application/json")
    assert res.status_code == 400 # Response returned

@pytest.mark.django_db
def test_character_initiative_endpoint_float_initiative_rejected(client, combatant):
    res = client.patch(reverse('core:update_initiative', args=[combatant.pk]), {"initiative": 10.9}, content_type="application/json")
    assert res.status_code == 400 # Response returned

@pytest.mark.django_db
def test_character_initiative_endpoint_float_initiative_accepted(client, combatant):
    res = client.patch(reverse('core:update_initiative', args=[combatant.pk]), {"initiative": 10.0}, content_type="application/json")
    assert res.status_code == 200 # Response returned

@pytest.mark.django_db
def test_character_initiative_endpoint_string_initiative_rejected(client, combatant):
    res = client.patch(reverse('core:update_initiative', args=[combatant.pk]), {"initiative": "10"}, content_type="application/json")
    assert res.status_code == 400 # Response returned

@pytest.mark.django_db
def test_character_initiative_too_large_returns_max(client, combatant):
    res = client.patch(reverse('core:update_initiative', args=[combatant.pk]), {"initiative": 21}, content_type="application/json")
    assert res.status_code == 200 # Response returned
    assert res.json()["initiative"] == 20

    combatant.refresh_from_db()
    
@pytest.mark.django_db
def test_character_initiative_0_accepted(client, combatant):
    res = client.patch(reverse('core:update_initiative', args=[combatant.pk]), {"initiative": 0}, content_type="application/json")
    assert res.status_code == 200 # Response returned
    assert res.json()["initiative"] == 0

    combatant.refresh_from_db()
    assert combatant.initiative == 0


@pytest.mark.django_db
def test_character_name_update_trims_and_persists(client, combatant):
    response = client.patch(
        reverse("core:update_character_details", args=[combatant.pk]),
        {"name": "  Hobgoblin Captain  "},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {"name": "Hobgoblin Captain"}
    combatant.character.refresh_from_db()
    assert combatant.character.name == "Hobgoblin Captain"


@pytest.mark.parametrize(
    "field",
    [
        "strength_save_bonus",
        "dexterity_save_bonus",
        "constitution_save_bonus",
        "intelligence_save_bonus",
        "wisdom_save_bonus",
        "charisma_save_bonus",
    ],
)
@pytest.mark.django_db
def test_character_saving_throw_update_persists(client, combatant, field):
    response = client.patch(
        reverse("core:update_character_details", args=[combatant.pk]),
        {field: -3},
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json() == {field: -3}
    combatant.character.refresh_from_db()
    assert getattr(combatant.character, field) == -3


@pytest.mark.parametrize(
    "data",
    [
        {"name": " "},
        {"name": "x" * 121},
        {"strength_save_bonus": 1.5},
        {"strength_save_bonus": True},
        {"strength_save_bonus": "2"},
        {"strength_save_bonus": 2**31},
        {"armor_class": 15},
        {"name": "New name", "strength_save_bonus": 2},
    ],
)
@pytest.mark.django_db
def test_invalid_character_detail_update_does_not_change_character(client, combatant, data):
    response = client.patch(
        reverse("core:update_character_details", args=[combatant.pk]),
        data,
        content_type="application/json",
    )

    assert response.status_code == 400
    combatant.character.refresh_from_db()
    assert combatant.character.name == "Goblin"
    assert combatant.character.strength_save_bonus == 0


@pytest.mark.django_db
def test_encounter_card_renders_clickable_character_fields(client, combatant):
    response = client.get(reverse("core:encounter", args=[combatant.encounter_id]))

    assert response.status_code == 200
    assert b'data-character-field="name"' in response.content
    assert b'data-character-field="strength_save_bonus"' in response.content
    assert b'data-update-character-url="/character/' in response.content
    assert b'aria-label="Edit combatant name: Goblin"' in response.content
