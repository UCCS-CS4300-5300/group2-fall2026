import json
import re

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from ..models import AttackDamage, CharacterAttack, CharacterEncounter, Encounter


DAMAGE_FORMULA = re.compile(r"^\s*(\d{1,2})d(4|6|8|10|12|20)(?:\s*([+-])\s*(\d{1,3}))?\s*$", re.IGNORECASE)
SAVE_ABILITIES = {"STR", "DEX", "CON", "INT", "WIS", "CHA"}


def serialize_attack(attack):
    return {
        "id": attack.pk,
        "name": attack.name,
        "description": attack.description,
        "attack_bonus": attack.attack_bonus,
        "dc": attack.dc,
        "dc_type": attack.dc_type,
        "dc_success": attack.dc_success,
        "damage_components": [
            {
                "damage_dice": component.damage_dice,
                "damage_modifier": component.damage_modifier,
                "damage_type": component.damage_type,
            }
            for component in attack.damage_components.all()
        ],
    }


@require_GET
def encounter_attacks(request, encounter_id):
    encounter = get_object_or_404(Encounter, pk=encounter_id)
    entries = (
        CharacterEncounter.objects.filter(encounter=encounter)
        .select_related("character")
        .prefetch_related("character__attacks__damage_components")
        .order_by("pk")
    )
    return JsonResponse({
        "characters": [
            {
                "entry_id": entry.pk,
                "name": entry.character.name,
                "attacks": [
                    serialize_attack(attack)
                    for attack in entry.character.attacks.all()
                ],
                "create_url": reverse(
                    "core:create_custom_attack",
                    kwargs={"encounter_id": encounter.pk, "entry_id": entry.pk},
                ),
            }
            for entry in entries
        ]
    })


@require_POST
def create_custom_attack(request, encounter_id, entry_id):
    entry = get_object_or_404(
        CharacterEncounter.objects.select_related("character"),
        pk=entry_id,
        encounter_id=encounter_id,
    )
    try:
        data = json.loads(request.body)
    except (TypeError, ValueError):
        return JsonResponse({"error": "Send valid JSON."}, status=400)
    if not isinstance(data, dict):
        return JsonResponse({"error": "Attack details must be an object."}, status=400)

    name = data.get("name")
    description = data.get("description", "")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 120:
        return JsonResponse({"error": "Name must contain 1 to 120 characters."}, status=400)
    if not isinstance(description, str) or len(description) > 4000:
        return JsonResponse({"error": "Description must be at most 4000 characters."}, status=400)

    attack_bonus = data.get("attack_bonus")
    dc = data.get("dc")
    if attack_bonus is not None and (type(attack_bonus) is not int or not -(2**31) <= attack_bonus < 2**31):
        return JsonResponse({"error": "Attack bonus must be a whole number."}, status=400)
    if dc is not None and (type(dc) is not int or not 1 <= dc < 2**31):
        return JsonResponse({"error": "Save DC must be a positive whole number."}, status=400)
    if (attack_bonus is None) == (dc is None):
        return JsonResponse({"error": "Provide either an attack bonus or a save DC."}, status=400)

    dc_type = data.get("dc_type", "")
    dc_success = data.get("dc_success", "")
    if dc is not None and (
        not isinstance(dc_type, str)
        or dc_type not in SAVE_ABILITIES
        or not isinstance(dc_success, str)
        or dc_success not in {"half", "none"}
    ):
        return JsonResponse({"error": "Choose a valid saving throw ability and success effect."}, status=400)

    damage_formula = data.get("damage_formula", "")
    damage_type = data.get("damage_type", "")
    if not isinstance(damage_formula, str) or len(damage_formula) > 50:
        return JsonResponse({"error": "Damage formula must be at most 50 characters."}, status=400)
    if not isinstance(damage_type, str) or len(damage_type) > 50:
        return JsonResponse({"error": "Damage type must be at most 50 characters."}, status=400)
    damage_formula = damage_formula.strip()
    damage_type = damage_type.strip()

    formula_match = DAMAGE_FORMULA.fullmatch(damage_formula) if damage_formula else None
    if damage_formula and not formula_match:
        return JsonResponse(
            {"error": "Damage must use a supported formula such as 2d6 + 3."},
            status=400,
        )

    damage_dice = None
    damage_modifier = 0
    if formula_match:
        count, sides, sign, modifier = formula_match.groups()
        if int(count) > 20:
            return JsonResponse({"error": "Damage formulas can roll at most 20 dice."}, status=400)
        damage_dice = f"{count}d{sides}"
        if modifier:
            damage_modifier = int(modifier) * (-1 if sign == "-" else 1)

    with transaction.atomic():
        attack = CharacterAttack.objects.create(
            character=entry.character,
            name=name.strip(),
            description=description,
            attack_bonus=attack_bonus,
            dc=dc,
            dc_type=dc_type if dc is not None else "",
            dc_success=dc_success if dc is not None else "",
        )
        if damage_dice:
            AttackDamage.objects.create(
                attack=attack,
                damage_dice=damage_dice,
                damage_modifier=damage_modifier,
                damage_type=damage_type,
            )

    return JsonResponse(serialize_attack(attack), status=201)
