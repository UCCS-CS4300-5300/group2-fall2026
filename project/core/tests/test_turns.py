import pytest
from django.urls import reverse

from ..models import Character, CharacterEncounter, Encounter


pytestmark = pytest.mark.django_db


def add_card(encounter, name, initiative=0):
    return CharacterEncounter.objects.create(
        encounter=encounter, character=Character.objects.create(name=name), initiative=initiative
    )


def post(client, route, encounter, data):
    return client.post(reverse("core:" + route, args=[encounter.pk]), data, content_type="application/json")


def test_round_uses_saved_rolls_and_breaks_ties_by_entry_id(client, encounter):
    first_guard = add_card(encounter, "Guard")
    second_guard = add_card(encounter, "Guard")
    dragon = add_card(encounter, "Dragon")
    rolls = {str(second_guard.pk): 12, str(dragon.pk): 19, str(first_guard.pk): 12}
    rolled = post(client, "roll_initiative", encounter, {"rolls": rolls})
    assert rolled.status_code == 200
    assert rolled.json() == {"rolls": rolls, "round": 1, "turn_version": 1, "turn_index": 0, "active_id": dragon.pk}

    for index, active_id, round_number in [(0, first_guard.pk, 1), (1, second_guard.pk, 1), (2, dragon.pk, 2)]:
        result = post(client, "next_turn", encounter, {"turn_version": index + 1}).json()
        assert (result["turn_index"], result["active_id"], result["round"]) == (index + 1, active_id, round_number)
    page = client.get(reverse("core:encounter", args=[encounter.pk]))
    assert page.context["turn"] == result


def test_single_combatant_wraps_and_a_retried_click_does_not_skip_a_round(client, encounter, combatant):
    advanced = post(client, "next_turn", encounter, {"turn_version": 0}).json()
    assert (advanced["turn_index"], advanced["round"], advanced["active_id"]) == (1, 2, combatant.pk)
    retry = post(client, "next_turn", encounter, {"turn_version": 0})
    assert retry.json() == advanced
    rerolled = post(client, "roll_initiative", encounter, {"rolls": {str(combatant.pk): 8}}).json()
    assert (rerolled["turn_index"], rerolled["round"]) == (0, 1)
    delayed_click = post(client, "next_turn", encounter, {"turn_version": 0})
    assert delayed_click.json() == rerolled


def test_empty_encounter_and_new_unrolled_combatant(client, encounter):
    blank = post(client, "next_turn", encounter, {"turn_version": 0})
    assert blank.json() == {"rolls": {}, "round": 0, "turn_index": 0, "turn_version": 0, "active_id": None}
    assert post(client, "roll_initiative", encounter, {"rolls": {}}).status_code == 400
    new_card = add_card(encounter, "Guard")
    assert post(client, "next_turn", encounter, {"turn_version": 0}).json()["active_id"] is None
    active = add_card(encounter, "Scoundrel", 7)
    next_round = post(client, "next_turn", encounter, {"turn_version": 0}).json()
    assert (next_round["active_id"], next_round["round"]) == (active.pk, 2)
    assert next_round["rolls"] == {str(new_card.pk): 0, str(active.pk): 7}


def test_roster_mismatch_preserves_turn_and_rolls_in_both_encounters(client, encounter, combatant):
    other = Encounter.objects.create(name="Cave")
    visitor = add_card(other, "Goblin", 9)
    before = post(client, "next_turn", encounter, {"turn_version": 0}).json()
    missing = add_card(encounter, "Ranger", 3)
    wrong_roster = {str(combatant.pk): 2, str(visitor.pk): 20}
    assert post(client, "roll_initiative", encounter, {"rolls": wrong_roster}).status_code == 409
    for card, value in [(combatant, 14), (visitor, 9), (missing, 3)]:
        card.refresh_from_db()
        assert card.initiative == value
    encounter.refresh_from_db()
    other.refresh_from_db()
    assert (encounter.turn_index, other.turn_index) == (before["turn_index"], 0)
    assert (encounter.turn_version, other.turn_version) == (before["turn_version"], 0)


@pytest.mark.parametrize("value", [0, 21, True, "12"])
def test_invalid_roll_does_not_save_other_rolls(client, encounter, combatant, value):
    second = add_card(encounter, "Wizard", 6)
    rolls = {str(combatant.pk): 19, str(second.pk): value}
    assert post(client, "roll_initiative", encounter, {"rolls": rolls}).status_code == 400
    combatant.refresh_from_db()
    second.refresh_from_db()
    assert (combatant.initiative, second.initiative) == (14, 6)
