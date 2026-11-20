import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.db.models import ProtectedError
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.template.loader import render_to_string

from ..forms import EncounterForm
from ..models import CharacterEncounter, Encounter, Quest
from .turns import turn_state

@require_http_methods(["GET", "DELETE", "PATCH"])
def encounter_detail(request, encounter_id):
    if request.method == "GET":
        return get_encounter(request, encounter_id)
    if request.method == "DELETE":
        return delete_encounter(request, encounter_id)
    if request.method == "PATCH":
        return update_encounter(request, encounter_id)

@require_http_methods(["PATCH"])
def update_encounter(request, encounter_id):
    # Empty request body means no-op
    if not request.body.strip():
        return HttpResponse(status=200)
    encounter = get_object_or_404(Encounter, pk=encounter_id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Unable to parse body as JSON"}, status=400) # Some other error
    # Empty dict means no-op
    if not data:
        return HttpResponse(status=200)
    
    form = EncounterForm(data, partial=True, instance=encounter)
    if not form.is_valid():
        return JsonResponse(form.errors, status=400)

    encounter = form.save()
    return HttpResponse(status=200)

@require_GET
def get_encounter(request, encounter_id):
    encounter = get_object_or_404(Encounter, pk=encounter_id)
    character_encounters = CharacterEncounter.objects.filter(encounter__pk=encounter_id)
    quests = Quest.objects.filter(encounter__pk=encounter_id).order_by("id")
    return render(
        request,
        "core/encounter.html",
        {
            "quests": quests,
            "items": character_encounters,
            "encounter": encounter,
            "turn": turn_state(encounter),
        }
    )

@require_http_methods(["DELETE"])
def delete_encounter(request, encounter_id):
    encounter = get_object_or_404(Encounter, pk=encounter_id)
    
    # Deletes encounter
    try:
        encounter.delete()
    except ProtectedError:
        return HttpResponse("Encounter is referenced by other records.", status=409)
        
    return HttpResponse(status=204)

@require_POST
def add_encounter(request):
    form = EncounterForm(request.POST)
    if not form.is_valid():
        return JsonResponse(form.errors, status=400)

    encounter = form.save()

    # Get HTML response for JavaScript
    html = render_to_string("core/dashboard_encounter_card.html", {"encounter":encounter})
    return HttpResponse(html)