from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_http_methods

import json

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
@require_http_methods(["PATCH"])
def update_hp(request, entry_id):
    # Get character-encounter to update its remaining hp
    char = get_object_or_404(CharacterEncounter, pk=entry_id)
    try:
        data = json.loads(request.body)
        new_hp = data["remaining_hp"]
    except (ValueError, TypeError, KeyError):
        return JsonResponse({"error": "remaining_hp field must be a valid integer"}, 400)

    char.remaining_hp = new_hp
    char.save(update_fields=["remaining_hp"])
    return JsonResponse({"remaining_hp": char.remaining_hp}, status=200)