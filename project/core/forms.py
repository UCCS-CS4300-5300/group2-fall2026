from django import forms
from .models import Character
from .models import Quest


class QuestForm(forms.ModelForm):
    class Meta:
        model = Quest
        fields = ["text"]


# Form for adding new character
class CharacterForm(forms.ModelForm):
    class Meta:
        model=Character
        fields=["name", "max_hp", "armor_class", "char_type"]
