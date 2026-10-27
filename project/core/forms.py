from django import forms
from .models import Character
from .models import Quest


class QuestForm(forms.ModelForm):
    class Meta:
        model = Quest
        fields = ["text"]


# Form for adding new character
class CharacterForm(forms.ModelForm):
    strength_save_bonus = forms.IntegerField(required=False, initial=0)
    dexterity_save_bonus = forms.IntegerField(required=False, initial=0)
    constitution_save_bonus = forms.IntegerField(required=False, initial=0)
    intelligence_save_bonus = forms.IntegerField(required=False, initial=0)
    wisdom_save_bonus = forms.IntegerField(required=False, initial=0)
    charisma_save_bonus = forms.IntegerField(required=False, initial=0)

    class Meta:
        model=Character
        fields=[
            "name",
            "max_hp",
            "armor_class",
            "char_type",
            "strength_save_bonus",
            "dexterity_save_bonus",
            "constitution_save_bonus",
            "intelligence_save_bonus",
            "wisdom_save_bonus",
            "charisma_save_bonus",
        ]

    def clean(self):
        cleaned_data = super().clean()
        for field_name in (
            "strength_save_bonus",
            "dexterity_save_bonus",
            "constitution_save_bonus",
            "intelligence_save_bonus",
            "wisdom_save_bonus",
            "charisma_save_bonus",
        ):
            if cleaned_data.get(field_name) is None:
                cleaned_data[field_name] = 0
        return cleaned_data
