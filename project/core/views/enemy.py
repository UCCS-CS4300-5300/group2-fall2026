import json
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.shortcuts import get_object_or_404
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from ..models import Character, CharacterEncounter, Encounter, CharacterAttack, AttackDamage

@require_GET
def search_enemy(request):
    query = request.GET.get("q", "").strip()

    # Return empty list if user doesnt enter search term 
    if not query:
        return JsonResponse({"monsters": []})

    # Bae URL for D&D 5e API
    base_url = "https://www.dnd5eapi.co/api/2014/monsters"

    try:
        # Search the API for monster matching the input
        search_url = f"{base_url}?{urlencode({'name': query})}"

        # Send search request and read JSON response
        with urlopen(search_url, timeout=10) as response:
            search_data = json.loads(response.read().decode("utf-8"))

        # Holds the monster info sent to JS
        monsters = []

        # Limit number of results to keep tab managable
        for result in search_data.get("results", [])[:5]:
            # Get API identifier for monster
            monster_index = result.get("index")

            # Skip Result if no identifier found
            if not monster_index:
                continue

            # Build URl for monster detail info
            monster_url = f"{base_url}/{monster_index}"

            # Request monsters full stats
            with urlopen(monster_url, timeout=10) as response:
                monster = json.loads(response.read().decode("utf-8")
            )

            # Extract numeric armor class
            armor_classes = monster.get("armor_class", [])
            armor_class = (
                armor_classes[0].get("value")
                if armor_classes
                else None
            )

            # Extract armor class type if available
            armor_class_type = ( 
                armor_classes[0].get("type")
                if armor_classes
                else None
            )

            # Get monster image path from API
            image = monster.get("image")

            # Turn image pth into URL
            if image and image.startswith("/"):
                image = f"https://www.dnd5eapi.co{image}"

            # Selecting fields needed by frontend
            monsters.append({
                "index": monster.get("index"),
                "name": monster.get("name"),
                "image": image,
                "size": monster.get("size"),
                "type": monster.get("type"),
                "alignment": monster.get("alignment"),
                # Send extracted values
                "armor_class": armor_class,
                "armor_class_type": armor_class_type,

                "hit_points": monster.get("hit_points"),
                "speed": monster.get("speed"),
                "challenge_rating": monster.get("challenge_rating"),
                "xp": monster.get("xp"),
                "strength": monster.get("strength"),
                "dexterity": monster.get("dexterity"),
                "constitution": monster.get("constitution"),
                "intelligence": monster.get("intelligence"),
                "wisdom": monster.get("wisdom"),
                "charisma": monster.get("charisma"),
                "actions": monster.get("actions", []),
            })

        # Return the list in format expected by enemy_presets.js
        return JsonResponse({"monsters": monsters})

    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, TypeError):
        return JsonResponse( # Return JSON error
            {"error": "Unable to retrieve monsters from API."},
            status=502,
        )


#
@require_POST
def import_enemy(request, encounter_id):
    monster_index = request.POST.get("monster_index", "").strip()

    if not monster_index:
        return JsonResponse({"error": "Missing monster identifer."}, status=400)

    monster_url = (f"https://www.dnd5eapi.co/api/2014/monsters/{monster_index}")

    try:
        with urlopen(monster_url, timeout=10) as response:
            monster = json.loads(response.read().decode("utf-8"))

    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return JsonResponse(
            {"error": "Could not retrive this monster from the API."},
            status=502,
        )

    armor_classes = monster.get("armor_class", [])
    armor_class = ( armor_classes[0].get("value", 10)
        if armor_classes
        else 10
    )

    # Calculate ability modifier using booundaries from models.py
    def get_modifier(score):
        for boundary, modifier in Character.ability_score_mod_boundaries.items():
            if score <= boundary:
                return modifier

        return 10

    # Calculate non-proficient saving throws
    abilities = [
        "strength",
        "dexterity",
        "constitution",
        "intelligence",
        "wisdom",
        "charisma",
    ]

    saving_throws = {}

    for ability in abilities:
        ability_score = monster.get(ability, 10)
        saving_throws[ability] = get_modifier(ability_score)

    # Match API ability abbreviations to Character model fields
    ability_names = {
        "STR": "strength",
        "DEX": "dexterity",
        "CON": "constitution",
        "INT": "intelligence",
        "WIS": "wisdom",
        "CHA": "charisma",
        "STRENGTH": "strength",
        "DEXTERITY": "dexterity",
        "CONSTITUTION": "constitution",
        "INTELLIGENCE": "intelligence",
        "WISDOM": "wisdom",
        "CHARISMA": "charisma",
    }

    # Extract saving throw bonuses
    for save in monster.get("proficiencies", []):
        name = save.get("proficiency", {}).get("name", "")

        if name.startswith("Saving Throw: "):
            ability = name.replace("Saving Throw: ", "").strip().upper()

            if ability in ability_names:
                field = ability_names[ability]
                saving_throws[field] = save.get("value", 0)
                print("MONSTER ABILITY SCORES:")
                print({
                    "strength": monster.get("strength"),
                    "dexterity": monster.get("dexterity"),
                    "constitution": monster.get("constitution"),
                    "intelligence": monster.get("intelligence"),
                    "wisdom": monster.get("wisdom"),
                    "charisma": monster.get("charisma"),
                })


    print("CALCULATED SAVING THROWS:", saving_throws)

    # Add character to encounter
    with transaction.atomic():
        # Create char
        character = Character.objects.create(
            name = monster.get("name", "Unknown monster"),
            char_type="enemy",
            max_hp=monster.get("hit_points") or 1,
            armor_class=armor_class,
    
            # Ability scores
            strength=monster.get("strength", 0),
            dexterity=monster.get("dexterity", 0),
            constitution=monster.get("constitution", 0),
            intelligence=monster.get("intelligence", 0),
            wisdom=monster.get("wisdom", 0),
            charisma=monster.get("charisma", 0),
    
            # Total saving throw modifiers
            strength_save_bonus=saving_throws["strength"],
            dexterity_save_bonus= saving_throws["dexterity"],
            constitution_save_bonus=saving_throws["constitution"],
            intelligence_save_bonus=saving_throws["intelligence"],
            wisdom_save_bonus=saving_throws["wisdom"],
            charisma_save_bonus=saving_throws["charisma"],
        )

        for action in monster.get("actions", []):
            dc_info = action.get("dc") or {}
            dc_type_info = dc_info.get("dc_type") or {}

            attack = CharacterAttack.objects.create(
                character=character,
                name=action.get("name", "Unknown attack"),
                description=action.get("desc", ""),
                attack_bonus=action.get("attack_bonus"),
                dc = dc_info.get("dc_value"),
                dc_type = dc_type_info.get("name", ""),
                dc_success = dc_info.get("success_type", ""),
            )

            for damage in action.get("damage", []):
                formula = (damage.get("damage_dice") or "").strip()

                match = re.search(r"\s*([+-])\s*(\d+)\s*$", formula)

                modifier = 0

                if match:
                    modifier = int(match.group(2))

                    if match.group(1) == "-":
                        modifier *= -1

                    dice = formula[:match.start()].strip()
                else:
                    dice = formula

                AttackDamage.objects.create(
                    attack=attack,
                    damage_dice=dice,
                    damage_modifier=modifier,
                    damage_type=damage.get("damage_type", {}).get("name", ""),
                )
        encounter = get_object_or_404(Encounter, pk=encounter_id)
        entry = CharacterEncounter.objects.create(
            character=character,
            encounter=encounter,
            remaining_hp=character.max_hp,
        )

    # Return combatant card HTML
    html = render_to_string(
        "core/encounter_combatant_card.html",
        {"entry": entry},
    )
    return HttpResponse(html)