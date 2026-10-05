from django import forms
from .models import Character

# Form for adding new character
class CharacterForm(forms.ModelForm):
    class Meta:
        model=Character
        fields=["name", "max_hp", "armor_class"]