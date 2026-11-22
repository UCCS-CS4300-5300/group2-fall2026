import json
import math

from django.db import transaction
from django.db.models import F
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods, require_POST

from ..forms import CharacterForm
from ..models import CharacterEncounter, Encounter
from .turns import turn_state

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


@require_POST
@transaction.atomic
def clear_combatants(request, encounter_id):
    updated = Encounter.objects.filter(pk=encounter_id).update(
        turn_index=0,
        turn_version=F("turn_version") + 1,
    )
    if not updated:
        raise Http404

    CharacterEncounter.objects.filter(encounter_id=encounter_id).delete()
    encounter = Encounter.objects.get(pk=encounter_id)
    return JsonResponse(turn_state(encounter))


@require_http_methods(["DELETE"])
@transaction.atomic
def remove_combatant(request, entry_id):
    initial_entry = get_object_or_404(
        CharacterEncounter.objects.only("encounter_id"), pk=entry_id
    )
    encounter = get_object_or_404(
        Encounter.objects.select_for_update(), pk=initial_entry.encounter_id
    )
    entry = get_object_or_404(
        CharacterEncounter, pk=entry_id, encounter=encounter
    )
    ordered_cards = list(
        CharacterEncounter.objects.filter(encounter=encounter)
        .order_by("-initiative", "pk")
        .values_list("pk", "initiative")
    )
    initiative_order = [
        card_id for card_id, initiative in ordered_cards if initiative != 0
    ]
    if entry_id in initiative_order:
        completed_rounds, current_position = divmod(
            encounter.turn_index, len(initiative_order)
        )
        removed_position = initiative_order.index(entry_id)
        if removed_position < current_position:
            current_position -= 1
        remaining_count = len(initiative_order) - 1
        encounter.turn_index = (
            completed_rounds * remaining_count + current_position
            if remaining_count
            else 0
        )

    encounter.turn_version += 1
    encounter.save(update_fields=["turn_index", "turn_version"])
    entry.delete()
    return JsonResponse(turn_state(encounter))


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
            Saved initiative and current turn state if response code == 200
'''
@require_http_methods(["PATCH"])
def update_initiative(request, entry_id):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            raise TypeError
        initiative = data["initiative"]
        if type(initiative) not in (int, float):
            raise TypeError
        if isinstance(initiative, float) and (
            not math.isfinite(initiative) or not initiative.is_integer()
        ):
            raise ValueError
        if initiative < -(2 ** 31):
            raise ValueError
    except (ValueError, TypeError, KeyError):
        return JsonResponse({"error": "initiative field must exist and be a valid integer"}, status=400)

    expected = data.get("turn_version")
    if "turn_version" in data and (type(expected) is not int or expected < 0):
        return JsonResponse({"error": "A nonnegative turn version is required."}, status=400)

    initiative = min(int(initiative), 20)
    initial_entry = get_object_or_404(
        CharacterEncounter.objects.only("encounter_id"), pk=entry_id
    )
    with transaction.atomic():
        # Take the encounter's write lock before reading the current turn.
        updated = Encounter.objects.filter(pk=initial_entry.encounter_id).update(
            turn_version=F("turn_version")
        )
        if not updated:
            raise Http404
        encounter = Encounter.objects.get(pk=initial_entry.encounter_id)
        combatant = get_object_or_404(CharacterEncounter, pk=entry_id, encounter=encounter)
        before = turn_state(encounter)
        if expected is not None and expected != encounter.turn_version:
            return JsonResponse({
                **before,
                "initiative": combatant.initiative,
                "error": "The turn changed. Check the current order and try again.",
            }, status=409)

        if initiative != combatant.initiative:
            combatant.initiative = initiative
            combatant.save(update_fields=["initiative"])
            order = list(
                encounter.character_encounters.exclude(initiative=0)
                .order_by("-initiative", "pk").values_list("pk", flat=True)
            )
            if order and before["active_id"] is not None:
                if before["active_id"] in order:
                    position = order.index(before["active_id"])
                else:
                    # Unsetting the current combatant moves to the next one.
                    previous_order = [
                        int(card_id) for card_id, score in before["rolls"].items() if score != 0
                    ]
                    position = previous_order.index(before["active_id"])
                encounter.turn_index = (before["round"] - 1) * len(order) + position
            else:
                encounter.turn_index = 0
            encounter.turn_version += 1
            encounter.save(update_fields=["turn_index", "turn_version"])

        return JsonResponse({**turn_state(encounter), "initiative": combatant.initiative})

