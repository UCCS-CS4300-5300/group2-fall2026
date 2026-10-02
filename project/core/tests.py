import pytest
from django.urls import reverse
from .models import Character
from .models import Player

@pytest.mark.django_db
def test_character_get_modifier():
    char=Character(strength=8)
    assert Character.get_modifier(char.strength) == -1