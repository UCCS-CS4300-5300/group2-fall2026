import json

from django.db import transaction
from django.db.models import Exists, F
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from ..models import CharacterEncounter, Encounter


def turn_state(encounter):
    cards = encounter.character_encounters.order_by("-initiative", "pk")
    entries = list(cards.values_list("pk", "initiative"))
    rolls = {str(entry_id): value for entry_id, value in entries}
    order = [entry_id for entry_id, value in entries if value != 0]
    round_number, active_id = 0, None
    if order:
        completed_rounds, position = divmod(encounter.turn_index, len(order))
        round_number, active_id = completed_rounds + 1, order[position]
    return {
        "turn_version": encounter.turn_version, "turn_index": encounter.turn_index,
        "round": round_number, "active_id": active_id, "rolls": rolls,
    }


def read_payload(request):
    try:
        data = json.loads(request.body)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


@require_POST
@transaction.atomic
def roll_initiative(request, encounter_id):
    rolls = read_payload(request).get("rolls")
    if not isinstance(rolls, dict) or not rolls:
        return JsonResponse({"error": "Add a combatant before rolling initiative."}, status=400)
    if any(type(value) is not int or not 1 <= value <= 20 for value in rolls.values()):
        return JsonResponse({"error": "Each initiative roll must be a whole number from 1 to 20."}, status=400)

    # Grab the encounter's write lock before checking the roster or changing any rolls.
    if not Encounter.objects.filter(pk=encounter_id).update(turn_index=0, turn_version=F("turn_version") + 1):
        raise Http404
    cards = list(CharacterEncounter.objects.filter(encounter_id=encounter_id).only("pk", "initiative"))
    if rolls.keys() != {str(card.pk) for card in cards}:
        transaction.set_rollback(True)
        return JsonResponse({"error": "The combatants changed. Refresh the encounter and roll again."}, status=409)
    for card in cards:
        card.initiative = rolls[str(card.pk)]
    CharacterEncounter.objects.bulk_update(cards, ["initiative"])
    return JsonResponse(turn_state(Encounter.objects.get(pk=encounter_id)))


@require_POST
@transaction.atomic
def next_turn(request, encounter_id):
    expected = read_payload(request).get("turn_version")
    if type(expected) is not int or expected < 0:
        return JsonResponse({"error": "A nonnegative turn version is required."}, status=400)
    eligible = CharacterEncounter.objects.filter(encounter_id=encounter_id).exclude(initiative=0)
    Encounter.objects.filter(
        Exists(eligible), pk=encounter_id, turn_version=expected
    ).update(turn_index=F("turn_index") + 1, turn_version=F("turn_version") + 1)
    encounter = get_object_or_404(Encounter.objects.select_for_update(), pk=encounter_id)
    return JsonResponse(turn_state(encounter))
