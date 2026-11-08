import pytest

from .models import Character, CharacterEncounter, Encounter

# Global fixtures
@pytest.fixture
def encounter():
    encounter = Encounter.objects.create(name="Forest", location="Trail")
    return encounter

@pytest.fixture
def combatant(encounter):
    character = Character.objects.create(name="Goblin", max_hp=12, armor_class=13)
    return CharacterEncounter.objects.create(
        character=character,
        encounter=encounter,
        remaining_hp=12,
        initiative=14,
        x_pos=50,
        y_pos=60,
    )