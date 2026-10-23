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

@pytest.mark.django_db
def test_character_hp_endpoint_valid_int_success(client, combatant):
    c = combatant
    res = client.patch(reverse('core:update_hp', args=[c.pk]), {"remaining_hp": 19}, content_type="application/json")
    assert res.status_code == 200 # Response returned
    assert res.json()["remaining_hp"] == 19 # Response is accurate

    c.refresh_from_db() # Get update
    assert c.remaining_hp == 19 # Database was updated

@pytest.mark.django_db
def test_character_hp_endpoint_invalid_key(client, combatant):
    res = client.patch(reverse('core:update_hp', args=[combatant.pk]), {"invalid": 19}, content_type="application/json")
    assert res.status_code == 400 # Response returned