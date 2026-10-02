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