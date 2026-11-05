from django import forms
from .models import Character
from .models import Encounter
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

# Form for adding new encounter
class EncounterForm(forms.ModelForm):
    class Meta:
        model=Encounter
        fields=[
            "name",
            "location",
            "description",
        ]

    def __init__(self, data=None, partial=False, *args, **kwargs):
        # Partial data means to ignore empty fields
        if partial:
            instance = kwargs.get('instance', None)
                
            # If data is submitted and we are updating an existing instance
            if data and instance:
                mutable_data = data.copy()
                
                for field_name in self.Meta.fields or self.fields:
                    # If the field was submitted and blank, revert it to the instance's current value
                    if field_name in mutable_data:
                        if mutable_data[field_name].strip() == "":
                            mutable_data[field_name] = getattr(instance, field_name)
                            
                    # No field was submitted, use default value
                    else:
                        mutable_data[field_name] = mutable_data[field_name] = getattr(instance, field_name)
                        
                data = mutable_data
            
        super().__init__(data, *args, **kwargs)