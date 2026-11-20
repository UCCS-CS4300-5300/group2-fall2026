import json
import math
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from django.db import transaction
from django.db.models import Count, ProtectedError, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from ..forms import CharacterForm, EncounterForm, QuestForm
from ..models import Character, CharacterEncounter, Encounter, Quest
from ..ai import parse_chat_request, ChatError
from ..turns import turn_state

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