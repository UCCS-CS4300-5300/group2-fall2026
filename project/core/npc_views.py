from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from .forms import NPCForm
from .models import NPC, Encounter


@require_http_methods(["GET", "POST"])
def npcs(request, encounter_id):
    if request.method == "GET":
        return render(request, "core/npc_list.html", {"npcs": NPC.objects.filter(encounter__pk=encounter_id).order_by("id")})

    form = NPCForm(request.POST)
    if not form.is_valid():
        return JsonResponse(form.errors, status=400)
    encounter = get_object_or_404(Encounter, pk=encounter_id)
    npc=form.save(commit=False)
    npc.encounter=encounter
    npc = form.save()
    return render(request, "core/npc_item.html", {"npc": npc}, status=201)


@require_http_methods(["POST", "DELETE"])
def npc_detail(request, npc_id):
    npc = get_object_or_404(NPC, pk=npc_id)
    if request.method == "DELETE":
        npc.delete()
        return HttpResponse(status=204)

    form = NPCForm(request.POST, instance=npc)
    if not form.is_valid():
        return JsonResponse(form.errors, status=400)
    npc = form.save()
    return render(request, "core/npc_item.html", {"npc": npc})
