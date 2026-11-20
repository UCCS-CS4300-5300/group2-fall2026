import json

from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.http import require_http_methods, require_POST

from ..forms import QuestForm
from ..models import Encounter, Quest

@require_POST
def add_quest(request, encounter_id):
    form = QuestForm(request.POST)
    if not form.is_valid():
        return JsonResponse(form.errors, status=400)

    with transaction.atomic():
        encounter = get_object_or_404(Encounter, pk=encounter_id)
        quest = form.save(commit=False)
        quest.encounter = encounter
        quest.save()

    html = render_to_string("core/quest_item.html", {"quest": quest})
    return HttpResponse(html, status=201)


@require_http_methods(["PATCH", "DELETE"])
def quest_detail(request, quest_id):
    quest = get_object_or_404(Quest, pk=quest_id)
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