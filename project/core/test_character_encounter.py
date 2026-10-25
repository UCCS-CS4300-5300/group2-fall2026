import pytest
import json

from django.urls import reverse

from .models import Character
from .models import Encounter
from .models import CharacterEncounter

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
    assert combatant.initiative == 20