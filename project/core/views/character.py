import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from ..models import Character, CharacterEncounter

@require_http_methods(["PATCH"])
def update_character_details(request, entry_id):
    combatant = get_object_or_404(
        CharacterEncounter.objects.select_related("character"), pk=entry_id
    )
    try:
        data = json.loads(request.body)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Send a valid character field update."}, status=400)

    if not isinstance(data, dict) or len(data) != 1:
        return JsonResponse(
            {"error": "Update exactly one character field at a time."}, status=400
        )

    field, value = next(iter(data.items()))
    save_fields = {
        "strength_save_bonus",
        "dexterity_save_bonus",
        "constitution_save_bonus",
        "intelligence_save_bonus",
        "wisdom_save_bonus",
        "charisma_save_bonus",
    }
    if field == "name":
        if not isinstance(value, str):
            return JsonResponse({"error": "Name must be text."}, status=400)
        value = value.strip()
        if not value or len(value) > Character._meta.get_field("name").max_length:
            return JsonResponse(
                {"error": "Name must contain 1 to 120 characters."}, status=400
            )
    elif field == "armor_class":
        if type(value) is not int or not 1 <= value < 2**31:
            return JsonResponse(
                {"error": "Armor class must be a positive whole number."}, status=400
            )
    elif field in save_fields:
        if type(value) is not int or not -(2**31) <= value < 2**31:
            return JsonResponse(
                {"error": "Saving throw bonus must be a whole number."}, status=400
            )
    else:
        return JsonResponse(
            {"error": "That character field cannot be edited."}, status=400
        )

    setattr(combatant.character, field, value)
    combatant.character.save(update_fields=[field])
    return JsonResponse({field: value})