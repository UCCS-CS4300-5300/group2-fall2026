from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_http_methods, require_GET
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

import json
import math

from .forms import QuestForm
from .models import Encounter
from .models import CharacterEncounter
from .models import Quest
from .models import Character

from .forms import CharacterForm

def home(request):
    entries = CharacterEncounter.objects.all()
    return render(
        request,
        "core/home.html",
        {
            "quests": Quest.objects.filter(encounter__name="test_encounter").order_by("id"),
            "items": entries,
        }
    )

@require_GET
def search_enemy(request):
    query = request.GET.get("q", "").strip()

    if not query:
        return JsonResponse({"monsters": []})

    base_url = "https://www.dnd5eapi.co/api/2014/monsters"

    try:
        # Search the API for monster matching the input
        search_url = f"{base_url}?{urlencode({'name': query})}"

        with urlopen(search_url, timeout=10) as response:
            search_data = json.loads(response.read().decode("utf-8"))

        monsters = []

        # Limit number of results to keep tab managable
        for result in search_data.get("results", [])[:5]:
            monster_index = result.get("index")

            if not monster_index:
                continue

            monster_url = f"{base_url}/{monster_index}"

            with urlopen(monster_url, timeout=10) as response:
                monster = json.loads(response.read().decode("utf-8")
            )

            armor_classes = monster.get("armor_class", [])
            armor_class = (
                armor_classes[0].get("value")
                if armor_classes
                else None
            )

            image = monster.get("image")

            if image and image.startswith("/"):
                image = f"https://www.dnd5eapi.co{image}"

            monsters.append({
                "name": monster.get("name"),
                "image": image,
                "size": monster.get("size"),
                "type": monster.get("type"),
                "alignment": monster.get("alignment"),
                "armor_class": monster.get("armor_class"),
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

        return JsonResponse({"monsters": monsters})

    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, TypeError):
        return JsonResponse(
            {"error": "Unable to retrieve monsters from API."},
            status=502,
        )



# View to add combatant to encounter.
@require_POST
def add_combatant(request):
    # TODO: This creates a new character every single time. In the future, we might want to have this allow a repeat character/character type.
    form=CharacterForm(request.POST)
    if not form.is_valid():
        return JsonResponse(form.errors, status=400)

    # Atomically add the "CharacterEncounter linking table"
    with transaction.atomic():
        encounter, _ = Encounter.objects.get_or_create(name="test_encounter") # This is a placeholder since we only have 1 encounter
        character = form.save()
        entry = CharacterEncounter.objects.create(
            character=character,
            encounter=encounter,
            remaining_hp=character.max_hp,
        )

    # Get HTML response for JavaScript
    html = render_to_string("core/encounter_combatant_card.html", {"entry":entry})
    return HttpResponse(html)

# View to move the location of a combatant/CharacterEncounter so the page "remembers" their last location
@require_http_methods(["PATCH"])
def move_combatant(request, entry_id):
    entry = get_object_or_404(CharacterEncounter, pk=entry_id)

    try:
        data = json.loads(request.body)
        x = int(data["x"])
        y = int(data["y"])
    except (ValueError, KeyError, TypeError):
        return JsonResponse({"error": "x and y are required integers"}, status=400)

    entry.x_pos = x
    entry.y_pos = y
    entry.save(update_fields=["x_pos", "y_pos"])
    return JsonResponse({"x": x, "y": y})


@require_POST
def add_quest(request):
    form = QuestForm(request.POST)
    if not form.is_valid():
        return JsonResponse(form.errors, status=400)

    with transaction.atomic():
        encounter, _ = Encounter.objects.get_or_create(name="test_encounter")
        quest = form.save(commit=False)
        quest.encounter = encounter
        quest.save()

    html = render_to_string("core/quest_item.html", {"quest": quest})
    return HttpResponse(html, status=201)


@require_http_methods(["PATCH", "DELETE"])
def quest_detail(request, quest_id):
    quest = get_object_or_404(Quest, pk=quest_id, encounter__name="test_encounter")
    if request.method == "DELETE":
        quest.delete()
        return HttpResponse(status=204)

    try:
        data = json.loads(request.body)
    except ValueError:
        return JsonResponse({"error": "Send completed as true or false."}, status=400)
    if not isinstance(data, dict) or not isinstance(data.get("completed"), bool):
        return JsonResponse({"error": "Send completed as true or false."}, status=400)

    quest.completed = data["completed"]
    quest.save(update_fields=["completed"])
    return JsonResponse({"completed": quest.completed})

# Endpoint to update character HP
# TODO: Make actual API documentation
'''
PATCH

Update's character's remaning HP for current encounter

EXPECTS:    {"remaining_hp": int}
RETURNS:    {"error": str} if response code == 400
            {"remaining_hp": int} if response code == 200
'''
@require_http_methods(["PATCH"])
def update_hp(request, entry_id):
    # Get character-encounter to update its remaining hp
    combatant = get_object_or_404(CharacterEncounter, pk=entry_id)
    try:
        data = json.loads(request.body)
        new_hp = data["remaining_hp"]
        if math.floor(new_hp) != new_hp: raise TypeError # Only numeric values representing integers should be allowed
    except (ValueError, TypeError, KeyError):
        return JsonResponse({"error": "remaining_hp field must exist and be a valid integer"}, status=400)

    # New HP can only max out at character's max
    new_hp = min(new_hp, combatant.character.max_hp)
    combatant.remaining_hp = new_hp
    combatant.save(update_fields=["remaining_hp"])
    return JsonResponse({"remaining_hp": combatant.remaining_hp}, status=200)