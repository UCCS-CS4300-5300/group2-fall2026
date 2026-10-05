from django.db import models


class Character(models.Model):
    # The boundaries for the ability score modifiers
    ability_score_mod_boundaries = {
        1: -5,
        3: -4,
        5: -3,
        7: -2,
        9: -1,
        11: 0,
        13: 1,
        15: 2,
        17: 3,
        19: 4,
        21: 5,
        23: 6,
        25: 7,
        27: 8,
        29: 9,
        30: 10
    }

    # Basic info
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    # Ability Scores
    strength = models.IntegerField(default=0)
    dexterity = models.IntegerField(default=0)
    constitution = models.IntegerField(default=0)
    intelligence = models.IntegerField(default=0)
    wisdom = models.IntegerField(default=0)
    charisma = models.IntegerField(default=0)
    armor_class = models.IntegerField(default=0)

    # Other info
    max_hp = models.IntegerField(default=0)

    # idk if this function should go somewhere else ?
    @staticmethod
    def get_modifier(ability_score):
        for s, m in Character.ability_score_mod_boundaries.items():
            if ability_score <= s:
                return m

    def __str__(self):
        return self.name


# Player and enemy classes just stubbed out for now
class Player(Character):
    pass


class Enemy(Character):
    pass


# Encounter class. Includes a list of multiple characters.
class Encounter(models.Model):
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=120)
    description = models.CharField(max_length=255, blank=True)

    # Each Encoutner can have multiple Characters, and each Character can be in multiple encounters.
    characters = models.ManyToManyField(
        Character, through="CharacterEncounter", related_name="encounters")

# Character-Encounter class. This is the linking table to Encounter and Character and holds instance-specific information
class CharacterEncounter(models.Model):
    # I just thought these looked best.
    DEFAULT_X=50
    DEFAULT_Y=50

    # Each hard is part of an encounter and refers to a character, so these are FKs
    encounter = models.ForeignKey(
        Encounter, on_delete=models.CASCADE, related_name="character_encounters")
    character = models.ForeignKey(
        Character, on_delete=models.CASCADE, related_name="character_encounters")

    # Card-specific information
    # This will be different in any encounter, so this lives here instead of character.
    remaining_hp = models.IntegerField(default=0)
    initiative = models.IntegerField(default=0)

    x_pos = models.IntegerField(default=DEFAULT_X)
    y_pos=models.IntegerField(default=DEFAULT_Y)
