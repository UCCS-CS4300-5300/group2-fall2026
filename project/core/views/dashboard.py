from django.db.models import Count, Q
from django.shortcuts import render
from django.views.decorators.http import require_GET

from ..models import Encounter

@require_GET
def dashboard(request):
    encounters = Encounter.objects.annotate(
        player_count=Count("characters", filter=Q(characters__char_type="player")),
        enemy_count=Count("characters", filter=Q(characters__char_type="enemy")),
    )
    return render(
        request,
        "core/dashboard.html",
        {
            "encounters": encounters
        }
    )