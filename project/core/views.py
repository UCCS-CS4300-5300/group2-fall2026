from django.shortcuts import get_object_or_404, redirect, render

from .forms import CombatantForm, EncounterForm
from .models import Encounter

def home(request):
    if request.method == "POST":
        form = EncounterForm(request.POST)
        if form.is_valid():
            encounter = form.save()
            return redirect("core:encounter_detail", encounter_id=encounter.id)
    else:
        form = EncounterForm()

    return render(
        request,
        "core/home.html",
        {
            "form": form,
            "encounters": Encounter.objects.all(),
        }
    )


def encounter_detail(request, encounter_id):
    encounter = get_object_or_404(Encounter, id=encounter_id)
    if request.method == "POST":
        form = CombatantForm(request.POST)
        if form.is_valid():
            combatant = form.save(commit=False)
            combatant.encounter = encounter
            combatant.save()
            return redirect("core:encounter_detail", encounter_id=encounter.id)
    else:
        form = CombatantForm()

    return render(
        request,
        "core/encounter_detail.html",
        {"encounter": encounter, "form": form},
    )
