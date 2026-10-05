from django import forms
from .models import Character

# Form for adding new character
class CharacterForm(forms.ModelForm):
    class Meta:
        model=Character
        fields=["name", "max_hp", "armor_class"]


class DiceRollForm(forms.Form):
    sides = forms.TypedChoiceField(
        choices=[(sides, f"d{sides}") for sides in (4, 6, 8, 10, 12, 20)],
        coerce=int,
        initial=20,
        label="Die",
        widget=forms.Select(attrs={"class": "form-select form-select-sm"}),
    )
    count = forms.IntegerField(
        min_value=1,
        max_value=20,
        initial=1,
        label="Number of dice",
        widget=forms.NumberInput(attrs={"class": "form-control form-control-sm"}),
    )
