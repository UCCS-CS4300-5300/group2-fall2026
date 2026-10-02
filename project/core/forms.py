from django import forms

from .models import Encounter, EncounterCombatant


class EncounterForm(forms.ModelForm):
    class Meta:
        model = Encounter
        fields = ["name", "notes"]
        labels = {"name": "Encounter name", "notes": "DM notes (optional)"}
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Goblin ambush"}),
            "notes": forms.Textarea(
                attrs={"rows": 4, "placeholder": "Location, story hooks, or anything to remember..."}
            ),
        }


class CombatantForm(forms.ModelForm):
    class Meta:
        model = EncounterCombatant
        fields = ["name", "role", "hit_points", "armor_class", "attack_bonus", "damage"]
        labels = {
            "name": "Name",
            "role": "Type",
            "hit_points": "Hit points",
            "armor_class": "Armor class",
            "attack_bonus": "Attack bonus",
            "damage": "Damage dice",
        }
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "e.g. Goblin 1"}),
            "hit_points": forms.NumberInput(attrs={"min": 1}),
            "armor_class": forms.NumberInput(attrs={"min": 0}),
            "attack_bonus": forms.NumberInput(),
            "damage": forms.TextInput(attrs={"placeholder": "e.g. 1d6+2"}),
        }