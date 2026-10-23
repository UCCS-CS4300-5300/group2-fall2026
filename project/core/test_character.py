import pytest

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
    test_char = combatant.character
    res = client.patch(reverse('core:update_hp', args=[test_char.pk]), {"hp": 19}, content_type="application/json")
    assert res.status_code == 200 # Response returned