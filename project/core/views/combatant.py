import json
import math

from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods, require_POST

from ..forms import CharacterForm
from ..models import CharacterEncounter, Encounter

# View to add combatant to encounter.
@require_POST
def add_combatant(request, encounter_id):
    # TODO: This creates a new character every single time. In the future, we might want to have this allow a repeat character/character type.
    form=CharacterForm(request.POST)
    if not form.is_valid():
        return JsonResponse(form.errors, status=400)

    # Atomically add the "CharacterEncounter linking table"
    with transaction.atomic():
        encounter = get_object_or_404(Encounter, pk=encounter_id)
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

# Endpoint to update character HP
# TODO: Make actual API documentation
'''
PATCH

Updates character's remaning HP for current encounter

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

# Endpoint to update character initiative for specified encounter
# TODO: Make actual API documentation
'''
PATCH

Updates character's initiative for current encounter

EXPECTS:    {"initiative": int}
RETURNS:    {"error": str} if response code == 400
            {"initiative": int} if response code == 200
'''
@require_http_methods(["PATCH"])
def update_initiative(request, entry_id):
    # Get character-encounter to update its initiative
    combatant = get_object_or_404(CharacterEncounter, pk=entry_id)
    try:
        data = json.loads(request.body)
        initiative = data["initiative"]
        if math.floor(initiative) != initiative: raise TypeError # Only numeric values representing integers should be allowed
    except (ValueError, TypeError, KeyError):
        return JsonResponse({"error": "initiative field must exist and be a valid integer"}, status=400)

    # Initiative can only max out at 20 necessarily
    initiative = min(initiative, 20)
    combatant.initiative = initiative
    combatant.save(update_fields=["initiative"])
    return JsonResponse({"initiative": combatant.initiative}, status=200)

