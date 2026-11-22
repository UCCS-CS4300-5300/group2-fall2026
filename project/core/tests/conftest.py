import pytest

from ..models import Character, CharacterEncounter, Encounter
from unittest.mock import patch
from ..ai import ollama_backend, gemini_backend

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

@pytest.fixture
def ollama_backend_active():
    with patch("core.views.ai.parse_chat_request", ollama_backend.parse_chat_request):
        yield

@pytest.fixture
def gemini_backend_active():
    with patch("core.views.ai.parse_chat_request", gemini_backend.parse_chat_request):
        yield