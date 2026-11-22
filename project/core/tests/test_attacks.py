import json

import pytest
from django.urls import reverse

from ..models import AttackDamage, Character, CharacterAttack, CharacterEncounter, Encounter


@pytest.mark.django_db
def test_encounter_attack_list_only_includes_current_combatants(client, encounter, combatant):
    attack = CharacterAttack.objects.create(
        character=combatant.character,
        name="Bite",
        attack_bonus=5,
    )
    AttackDamage.objects.create(
        attack=attack,
        damage_dice="1d6",
        damage_modifier=2,
        damage_type="Piercing",
    )
    other_encounter = Encounter.objects.create(name="Other encounter")
    other_character = Character.objects.create(name="Other creature")
    CharacterEncounter.objects.create(
        encounter=other_encounter,
        character=other_character,
    )

    response = client.get(reverse("core:encounter_attacks", args=[encounter.pk]))

    assert response.status_code == 200
    data = response.json()
    assert [character["name"] for character in data["characters"]] == ["Goblin"]
    assert data["characters"][0]["attacks"][0]["name"] == "Bite"
    assert data["characters"][0]["attacks"][0]["damage_components"] == [
        {
            "damage_dice": "1d6",
            "damage_modifier": 2,
            "damage_type": "Piercing",
        }
    ]


@pytest.mark.django_db
def test_create_custom_attack_for_current_combatant(client, encounter, combatant):
    response = client.post(
        reverse(
            "core:create_custom_attack",
            args=[encounter.pk, combatant.pk],
        ),
        data=json.dumps({
            "name": "Flame Bolt",
            "description": "A bolt of fire.",
            "attack_bonus": 6,
            "dc": None,
            "damage_formula": "2d6 + 3",
            "damage_type": "Fire",
        }),
        content_type="application/json",
    )

    assert response.status_code == 201
    attack = CharacterAttack.objects.get(character=combatant.character, name="Flame Bolt")
    assert attack.attack_bonus == 6
    assert attack.damage_components.get().damage_dice == "2d6"
    assert attack.damage_components.get().damage_modifier == 3
    assert attack.damage_components.get().damage_type == "Fire"


@pytest.mark.django_db
def test_create_custom_save_attack(client, encounter, combatant):
    response = client.post(
        reverse(
            "core:create_custom_attack",
            args=[encounter.pk, combatant.pk],
        ),
        data=json.dumps({
            "name": "Frost Breath",
            "attack_bonus": None,
            "dc": 14,
            "dc_type": "CON",
            "dc_success": "half",
            "damage_formula": "1d8",
            "damage_type": "Cold",
        }),
        content_type="application/json",
    )

    assert response.status_code == 201
    attack = CharacterAttack.objects.get(character=combatant.character, name="Frost Breath")
    assert attack.attack_bonus is None
    assert attack.dc == 14
    assert attack.dc_type == "CON"
    assert attack.dc_success == "half"


@pytest.mark.django_db
def test_custom_attack_cannot_be_added_for_character_outside_encounter(client, encounter):
    other_encounter = Encounter.objects.create(name="Other encounter")
    character = Character.objects.create(name="Other creature")
    entry = CharacterEncounter.objects.create(
        encounter=other_encounter,
        character=character,
    )

    response = client.post(
        reverse(
            "core:create_custom_attack",
            args=[encounter.pk, entry.pk],
        ),
        data=json.dumps({
            "name": "Bite",
            "attack_bonus": 3,
            "dc": None,
        }),
        content_type="application/json",
    )

    assert response.status_code == 404
    assert not CharacterAttack.objects.filter(character=character).exists()


@pytest.mark.django_db
def test_custom_attack_rejects_invalid_damage_formula(client, encounter, combatant):
    response = client.post(
        reverse(
            "core:create_custom_attack",
            args=[encounter.pk, combatant.pk],
        ),
        data=json.dumps({
            "name": "Broken Attack",
            "attack_bonus": 3,
            "dc": None,
            "damage_formula": "lots of damage",
        }),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert not CharacterAttack.objects.filter(name="Broken Attack").exists()
