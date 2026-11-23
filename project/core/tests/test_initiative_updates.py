import json

import pytest
from django.urls import reverse

from ..models import Character, CharacterEncounter


pytestmark = pytest.mark.django_db


def add_card(encounter, name, initiative):
    return CharacterEncounter.objects.create(
        encounter=encounter,
        character=Character.objects.create(name=name),
        initiative=initiative,
    )


def edit(client, card, data):
    return client.patch(
        reverse("core:update_initiative", args=[card.pk]), json.dumps(data),
        content_type="application/json",
    )


def next_turn(client, encounter, version):
    return client.post(
        reverse("core:next_turn", args=[encounter.pk]), {"turn_version": version},
        content_type="application/json",
    ).json()


@pytest.mark.parametrize("score", [20, 3, 12])
def test_late_combatant_joins_without_changing_current_turn(client, encounter, score):
    first = add_card(encounter, "Ranger", 18)
    current = add_card(encounter, "Wizard", 12)
    last = add_card(encounter, "Guard", 6)
    newcomer = add_card(encounter, "Goblin", 0)
    encounter.turn_index = 4
    encounter.turn_version = 8
    encounter.save()

    response = edit(client, newcomer, {"initiative": score, "turn_version": 8})

    assert response.status_code == 200
    saved = response.json()
    assert (saved["active_id"], saved["round"], saved["turn_version"]) == (current.pk, 2, 9)
    assert saved["rolls"] == {
        str(first.pk): 18, str(current.pk): 12, str(last.pk): 6, str(newcomer.pk): score,
    }
    newcomer.refresh_from_db()
    assert newcomer.initiative == score
    page = client.get(reverse("core:encounter", args=[encounter.pk]))
    assert page.context["turn"] == {key: value for key, value in saved.items() if key != "initiative"}

    next_state = next_turn(client, encounter, 9)
    assert next_state["active_id"] == (newcomer.pk if score == 12 else last.pk)
    assert next_state["round"] == 2


@pytest.mark.parametrize("score, next_round", [(20, 2), (3, 3)])
def test_editing_active_score_keeps_its_turn(client, encounter, score, next_round):
    first = add_card(encounter, "Ranger", 18)
    current = add_card(encounter, "Wizard", 12)
    add_card(encounter, "Guard", 6)
    encounter.turn_index = 4
    encounter.save()

    saved = edit(client, current, {"initiative": score}).json()

    assert (saved["active_id"], saved["round"]) == (current.pk, 2)
    advanced = next_turn(client, encounter, saved["turn_version"])
    assert advanced["active_id"] == first.pk
    assert advanced["round"] == next_round


@pytest.mark.parametrize("removed_position", [0, 1, 2])
def test_unsetting_initiative_follows_removing_a_combatant(client, encounter, removed_position):
    cards = [add_card(encounter, name, score) for name, score in [("Ranger", 18), ("Wizard", 12), ("Guard", 6)]]
    encounter.turn_index = 4
    encounter.save()

    saved = edit(client, cards[removed_position], {"initiative": 0}).json()

    assert saved["round"] == 2
    assert saved["active_id"] == cards[2 if removed_position == 1 else 1].pk
    assert saved["rolls"][str(cards[removed_position].pk)] == 0


def test_unsetting_last_active_combatant_wraps_to_next_round(client, encounter):
    first = add_card(encounter, "Ranger", 18)
    last = add_card(encounter, "Guard", 6)
    encounter.turn_index = 3
    encounter.save()

    saved = edit(client, last, {"initiative": 0}).json()

    assert (saved["active_id"], saved["round"], saved["turn_index"]) == (first.pk, 3, 2)


def test_unsetting_only_combatant_and_assigning_first_score(client, combatant):
    encounter = combatant.encounter
    encounter.turn_index = 7
    encounter.save()

    cleared = edit(client, combatant, {"initiative": 0}).json()
    assert (cleared["active_id"], cleared["round"], cleared["turn_index"]) == (None, 0, 0)

    assigned = edit(client, combatant, {"initiative": 9}).json()
    assert (assigned["active_id"], assigned["round"], assigned["turn_index"]) == (combatant.pk, 1, 0)
    assert assigned["turn_version"] == 2


def test_edit_invalidates_old_next_turn_and_stale_edits(client, combatant):
    saved = edit(client, combatant, {"initiative": 10, "turn_version": 0}).json()
    retried_turn = next_turn(client, combatant.encounter, 0)
    assert retried_turn == {key: value for key, value in saved.items() if key != "initiative"}

    stale = edit(client, combatant, {"initiative": 5, "turn_version": 0})
    assert stale.status_code == 409
    assert stale.json()["error"]
    assert {key: value for key, value in stale.json().items() if key != "error"} == saved
    combatant.refresh_from_db()
    assert combatant.initiative == 10


def test_same_score_does_not_invalidate_turn(client, combatant):
    saved = edit(client, combatant, {"initiative": 14.0, "turn_version": 0}).json()
    assert saved["initiative"] == 14
    assert saved["turn_version"] == 0
    advanced = next_turn(client, combatant.encounter, 0)
    assert (advanced["round"], advanced["turn_version"]) == (2, 1)


@pytest.mark.parametrize("data", [
    [], None, {}, {"initiative": None}, {"initiative": True}, {"initiative": "10"},
    {"initiative": []}, {"initiative": {}}, {"initiative": 2.5}, {"initiative": -2147483649},
    {"initiative": float("inf")}, {"initiative": float("-inf")}, {"initiative": float("nan")},
    {"initiative": 8, "turn_version": -1}, {"initiative": 8, "turn_version": True},
    {"initiative": 8, "turn_version": None}, {"initiative": 8, "turn_version": "0"},
])
def test_bad_input_leaves_score_and_turn_unchanged(client, combatant, data):
    response = edit(client, combatant, data)

    assert response.status_code == 400
    combatant.refresh_from_db()
    combatant.encounter.refresh_from_db()
    assert combatant.initiative == 14
    assert (combatant.encounter.turn_index, combatant.encounter.turn_version) == (0, 0)


def test_legacy_negative_score_is_still_allowed(client, combatant):
    response = edit(client, combatant, {"initiative": -2})
    assert response.status_code == 200
    assert response.json()["initiative"] == -2
    combatant.refresh_from_db()
    assert combatant.initiative == -2
