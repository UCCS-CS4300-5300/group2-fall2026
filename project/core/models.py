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
    name=models.CharField(max_length=120)
    description=models.TextField(blank=True)

    # Ability Scores
    strength=models.IntegerField(default=0)
    dexterity=models.IntegerField(default=0)
    constitution=models.IntegerField(default=0)
    intelligence=models.IntegerField(default=0)
    wisdom=models.IntegerField(default=0)
    charisma=models.IntegerField(default=0)

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


class Encounter(models.Model):
    name = models.CharField(max_length=120)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.name


class EncounterCombatant(models.Model):
    PLAYER = "player"
    ENEMY = "enemy"
    ROLE_CHOICES = [(PLAYER, "Player"), (ENEMY, "Enemy")]

    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name="combatants")
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=12, choices=ROLE_CHOICES)
    hit_points = models.PositiveIntegerField()
    armor_class = models.PositiveIntegerField(default=10)
    attack_bonus = models.IntegerField(default=0)
    damage = models.CharField(max_length=24, default="1d6")

    class Meta:
        ordering = ["role", "id"]

    def __str__(self):
        return self.name