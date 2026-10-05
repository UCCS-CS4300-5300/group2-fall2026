from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from .models import Encounter
from .models import CharacterEncounter

from .forms import CharacterForm

def home(request):
    entries = CharacterEncounter.objects.all()
    return render(
        request,
        "core/home.html",
        {
            "items": entries
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