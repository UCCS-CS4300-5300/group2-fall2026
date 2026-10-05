from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_http_methods

import json
import random

from .models import Encounter
from .models import CharacterEncounter

from .forms import CharacterForm, DiceRollForm

def home(request):
    entries = CharacterEncounter.objects.all()
    return render(
        request,
        "core/home.html",
        {
            "items": entries,
            "dice_form": DiceRollForm(),
        }
    )


@require_POST
def roll_dice(request):
    form = DiceRollForm(request.POST)
    if not form.is_valid():
        return JsonResponse(form.errors, status=400)

    sides = form.cleaned_data["sides"]
    count = form.cleaned_data["count"]
    rolls = [random.randint(1, sides) for _ in range(count)]
    return JsonResponse({
        "sides": sides,
        "count": count,
        "rolls": rolls,
        "total": sum(rolls),
    })


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
