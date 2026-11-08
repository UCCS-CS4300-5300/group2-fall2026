import json
import pytest
from unittest.mock import patch, MagicMock
from urllib.error import URLError, HTTPError
from io import BytesIO

from django.urls import reverse
from core.models import Character, Encounter, CharacterEncounter

def mock_api_response(data):
    """Create a fake API response containing JSON data. """
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(data).encode("utf-8")
    return response


# Test 1 searching without a query retruns HTTP 400
def test_search_without_query(client):
    response = client.get(reverse("core:search_enemy"))

    assert response.status_code == 200

#Test 2: A successful search returns monster data
@patch("core.views.urlopen")
def test_search_returns_monsters(mock_urlopen, client):
    search_results = { 
        "results": [
            {"index": "goblin", "name": "Goblin"}
        ]
    }

    monster_details = {
        "index": "goblin",
        "name": "Goblin",
        "size": "Small",
        "type": "humanoid",
        "alignment": "neutral evil",
        "armor_class": [
            {
                "value": 15,
                "type": "armor",
                "desc": "leather armor, shield",
            }
        ],
        "hit_points": 7,
        "challenge_rating": 0.25,
        "xp": 50,
        "speed": {"walk": "30 ft."},
        "strength": 8,
        "dexterity": 14,
        "constitution": 10,
        "wisdom": 8,
        "charisma": 8,
        "actions": [],
    }

    mock_urlopen.side_effect = [
        mock_api_response(search_results),
        mock_api_response(monster_details),
    ]

    url = reverse("core:search_enemy")
    response = client.get(url, {"q": "Goblin"})

    assert response.status_code == 200
    data = response.json()
    assert "monsters" in data
    assert len(data["monsters"]) == 1
    assert data["monsters"][0]["name"] == "Goblin"

# Test 3: A search with no matches returns an empty list
@patch("core.views.urlopen")
def test_search_returns_empty_list(mock_urlopen, client):
    mock_urlopen.return_value = mock_api_response({
        "results": []
    })

    response = client.get(
        reverse("core:search_enemy")
    )

    assert response.status_code == 200
    assert response.json()["monsters"] == []


# Test 4 A network failure returns HTTP 502
@patch("core.views.urlopen")
def test_api_connection_error_returns_502(mock_urlopen, client):
    mock_urlopen.side_effect = URLError("Connection failed")
    url = reverse("core:search_enemy")
    response = client.get(url, {"q": "Goblin"})

# Test 5: POST requests not allowed
def test_post_request_is_not_allowed(client):
    url = reverse("core:search_enemy")
    response = client.post(url, {"q": "Goblin"})
    assert response.status_code == 405

# Test 6: Whitespace only query - confirms .strip() handles blank searches
def test_search_with_whitespace_query(client):
    url = reverse("core:search_enemy")
    response = client.get(url, {"q": f"\n\t   "})

    assert response.status_code == 200
    assert response.json() == {"monsters": []}

# Test 7: Invalid JSON from the API - tests error handling 
@patch("core.views.urlopen")
def test_invaid_api_json(mock_urlopen, client):
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = b"not valid json"

    mock_urlopen.return_value = mock_response

    url = reverse("core:search_enemy")
    response = client.get(url, {"q": "Goblin"})

    assert response.status_code == 502


# Test 8 API returns HTTP error
@patch("core.views.urlopen")
def test_api_http_error(mock_urlopen, client):
    mock_urlopen.side_effect = HTTPError(
        url="https://www.dnd5eapi.co/api/2014/monsters",
        code=500,
        msg="Server Error",
        hdrs=None,
        fp=None,
    )

    url = reverse("core:search_enemy")
    response = client.get(url, {"q": "Goblin"})

    assert response.status_code == 502

# Test 9: Monster with missing optional fields
@patch("core.views.urlopen")
def test_monster_missing_optional_fields(mock_urlopen, client):
    search_data = {
        "results": [{"index": "goblin", "name": "Goblin"}]
    }

    monster_data = {
        "index": "goblin",
        "name": "Goblin"
    }

    mock_urlopen.side_effect = [
        mock_api_response(search_data),
        mock_api_response(monster_data),
    ]

    url = reverse("core:search_enemy")
    response = client.get(url, {"q": "Goblin"})

    assert response.status_code == 200
    assert response.json()["monsters"][0]["name"] == "Goblin"

# Test 10: Result limit
@patch("core.views.urlopen")
def test_search_returns_at_most_five_monsters(mock_urlopen, client):
    search_data = {
        "results": [
            {"index": f"monster-{i}", "name": f"Monster {i}"}
            for i in range(7)
        ]
    }

    mock_urlopen.side_effect = [
        mock_api_response(search_data),
        *[
            mock_api_response({
                "index": f"monster-{i}",
                "name": f"Monster {i}",
            })
            for i in range(5)
        ],
    ]

    url = reverse("core:search_enemy")
    response = client.get(url, {"q": "Goblin"})

    assert response.status_code == 200
    assert len(response.json()["monsters"]) <= 5

#---------------------------------------------------------------------------
# Tests for saving throws and import
#---------------------------------------------------------------------------

# Helper to mock the API response for the following tests easier than
# what i did in the previous tests bc i can keep calling this when 
# needed and dont have to keep writing the same thing in different tests
def mock_monster_api(monkeypatch, monster_data):
    def fake_urlopen(url, timeout=10):
        return BytesIO(json.dumps(monster_data).encode("utf-8"))

    monkeypatch.setattr("core.views.urlopen", fake_urlopen)

# Test 1: Test Adult Black Dragon saving throws
@pytest.mark.django_db
def test_import_adult_black_dragon_saving_throws(client, monkeypatch, encounter):
    monster_data = {
        "name": "Adult Black Dragon",
        "hit_points": 195,
        "armor_class": [{"value": 19}],
        "strength": 23,
        "dexterity": 14,
        "constitution": 21,
        "intelligence": 14,
        "wisdom": 13,
        "charisma": 17,
        "proficiencies": [
            {"proficiency": {"name": "Saving Throw: DEX"}, "value": 7},
            {"proficiency": {"name": "Saving Throw: CON"}, "value": 10},
            {"proficiency": {"name": "Saving Throw: WIS"}, "value": 6},
            {"proficiency": {"name": "Saving Throw: CHA"}, "value": 8},
        ],
    }

    mock_monster_api(monkeypatch, monster_data)

    response = client.post(
        reverse("core:import_enemy", kwargs={"encounter_id": encounter.pk}),
        {"monster_index": "adult-black-dragon"},
    )

    assert response.status_code == 200

    character_encounter = CharacterEncounter.objects.get(character__name="Adult Black Dragon", encounter__pk=encounter.pk)
    dragon = character_encounter.character

    assert dragon.dexterity_save_bonus == 7
    assert dragon.constitution_save_bonus == 10
    assert dragon.wisdom_save_bonus == 6
    assert dragon.charisma_save_bonus == 8
    assert dragon.strength_save_bonus == 6
    assert dragon.intelligence_save_bonus == 2


# Test 2: Testing a monster with no saving throw proficiencies
# Checks to see if no proficient saves utilize ability modifer
@pytest.mark.django_db
def test_import_monster_without_saving_throws(client, monkeypatch):
    monster_data = {
        "name": "Goblin",
        "hit_points": 7,
        "armor_class": [{"value": 15}],
        "strength": 8,
        "dexterity": 14,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 8,
        "charisma": 8,
        "proficiencies": [],
    }

    mock_monster_api(monkeypatch, monster_data)

    response = client.post(
        "/api/enemies/import/",
        {"monster_index": "goblin"},
    )

    assert response.status_code == 200

    goblin = Character.objects.get(name="Goblin")

    assert goblin.strength_save_bonus == -1
    assert goblin.dexterity_save_bonus == 2
    assert goblin.constitution_save_bonus == 0
    assert goblin.intelligence_save_bonus == 0
    assert goblin.wisdom_save_bonus == -1
    assert goblin.charisma_save_bonus == -1

# Test 3: Testing monster with only some saving throws
# Checks if the proficient saving throws use API and 
# other saving throws use normal ability modifers
@pytest.mark.django_db
def test_import_partial_saving_throws(client, monkeypatch):
    monster_data = {
        "name": "Test Monster",
        "hit_points": 30,
        "armor_class": [{"value": 14}],
        "strength": 8,
        "dexterity": 14,
        "constitution": 12,
        "intelligence": 16,
        "wisdom": 10,
        "charisma": 18,
        "proficiencies": [
            {"proficiency": {"name": "Saving Throw: STR"}, "value": 5},
            {"proficiency": {"name": "Saving Throw: CHA"}, "value": 7},
        ],
    }

    mock_monster_api(monkeypatch, monster_data)

    response = client.post(
        "/api/enemies/import/",
        {"monster_index": "goblin"},
    )

    assert response.status_code == 200

    monster = Character.objects.get(name="Test Monster")

    assert monster.strength_save_bonus == 5
    assert monster.dexterity_save_bonus == 2
    assert monster.constitution_save_bonus == 1
    assert monster.intelligence_save_bonus == 3
    assert monster.wisdom_save_bonus == 0
    assert monster.charisma_save_bonus == 7

# Test 4: Negative saving throw bonus
# Checks if negative saving throws are correctly imported.
@pytest.mark.django_db
def test_import_negative_saving_throw(client, monkeypatch):
    monster_data = {
        "name": "Test Monster",
        "hit_points": 20,
        "armor_class": [{"value": 12}],
        "strength": 8,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10,
        "proficiencies": [
            {"proficiency": {"name": "Saving Throw: STR"}, "value": -1},
        ],
    }

    mock_monster_api(monkeypatch, monster_data)

    response = client.post(
        "/api/enemies/import/",
        {"monster_index": "test-monster"},
    )
    assert response.status_code == 200

    monster = Character.objects.get(name="Test Monster")

    assert monster.strength_save_bonus == -1


# Test 5: missing monster index
# Checks if import rejects the request that has no index
@pytest.mark.django_db
def test_import_missing_index(client):
    response = client.post("/api/enemies/import/", {})

    assert response.status_code == 400
    assert Character.objects.count() == 0

# Test 6: API error
# Checks
@pytest.mark.django_db
def test_import_api_error(client, monkeypatch):
    def fake_urlopen(url, timeout=10):
        raise HTTPError(url, 404, "Not Found", {}, None)

    monkeypatch.setattr("core.views.urlopen", fake_urlopen)

    response = client.post(
        "/api/enemies/import/",
        {"monster_index": "invalid-monster"},
    )

    assert response.status_code == 502
    assert Character.objects.count() == 0

# Test 7: Test ability modifer boundary
# Check if get_modifer calculation handles boundary values
@pytest.mark.django_db
def test_import_ability_modifier_boundary(client, monkeypatch):
    monster_data = {
        "name": "Boundary Monster",
        "hit_points": 50,
        "armor_class": [{"value": 15}],
        "strength": 1,
        "dexterity":3,
        "constitution": 11,
        "intelligence": 19,
        "wisdom": 30,
        "charisma": 25,
        "proficiencies": [],
    }

    mock_monster_api(monkeypatch, monster_data)

    response = client.post(
        "/api/enemies/import/",
        {"monster_index": "boundary-monster"},
    )

    assert response.status_code == 200

    monster = Character.objects.get(name="Boundary Monster")

    assert monster.strength_save_bonus == -5
    assert monster.dexterity_save_bonus == -4
    assert monster.constitution_save_bonus == 0
    assert monster.intelligence_save_bonus == 4
    assert monster.wisdom_save_bonus == 10
    assert monster.charisma_save_bonus == 7

# Test 8: Adult Bronze Dragon saving throws
# This checks another combination of ability and proficiencies
@pytest.mark.django_db
def test_import_adult_bronze_dragon_saves(client, monkeypatch):
    monster_data = {
        "name": "Adult Bronze Dragon",
        "hit_points": 212,
        "armor_class": [{"value": 19}],
        "strength": 23,
        "dexterity": 10,
        "constitution": 21,
        "intelligence": 16,
        "wisdom": 15,
        "charisma": 19,
        "proficiencies": [
            {"proficiency": {"name": "Saving Throw: DEX"}, "value": 5},
            {"proficiency": {"name": "Saving Throw: CON"}, "value": 10},
            {"proficiency": {"name": "Saving Throw: WIS"}, "value": 7},
            {"proficiency": {"name": "Saving Throw: CHA"}, "value": 9},
        ],
    }

    mock_monster_api(monkeypatch, monster_data)

    response = client.post(
        "/api/enemies/import/",
        {"monster_index": "boundary-monster"},
    )

    assert response.status_code == 200

    dragon = Character.objects.get(name="Adult Bronze Dragon")

    assert dragon.strength_save_bonus == 6
    assert dragon.dexterity_save_bonus == 5
    assert dragon.constitution_save_bonus == 10
    assert dragon.intelligence_save_bonus == 3
    assert dragon.wisdom_save_bonus == 7
    assert dragon.charisma_save_bonus == 9


# Test 9: Missing ability score
# Checks if the missing score defaults to 10 and 
# displays modifer of 0
@pytest.mark.django_db
def test_import_missing_ability_scores(client, monkeypatch):
    monster_data = {
        "name": "Missing Stats Monster",
        "hit_points": 20,
        "armor_class": [{"value": 12}],
        "proficiencies": [],
    }

    mock_monster_api(monkeypatch, monster_data)

    response = client.post(
        "/api/enemies/import/",
        {"monster_index": "missing-stats"},
    )

    assert response.status_code == 200

    monster = Character.objects.get(name="Missing Stats Monster")

    assert monster.strength_save_bonus == 0
    assert monster.dexterity_save_bonus == 0
    assert monster.constitution_save_bonus == 0
    assert monster.intelligence_save_bonus == 0
    assert monster.wisdom_save_bonus == 0
    assert monster.charisma_save_bonus == 0


# Test 10: Missing armor class
# Checks if a monster with no armor class defaults to 10
@pytest.mark.django_db
def test_import_missing_armor_class(client, monkeypatch):
    monster_data = {
        "name": "No Armor Monster",
        "hit_points": 20,
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10,
        "proficiencies": [],
    }

    mock_monster_api(monkeypatch, monster_data)

    response = client.post(
        "/api/enemies/import/",
        {"monster_index": "no-armor"},
    )

    assert response.status_code == 200

    monster = Character.objects.get(name="No Armor Monster")

    assert monster.armor_class == 10

# Test 11: Missing hit points
# Checks if a monster without hit points defaults to 0
@pytest.mark.django_db
def test_import_missing_hit_points(client, monkeypatch):
    monster_data = {
        "name": "No HP Monster",
        "armor_class": [{"value": 12}],
        "strength": 10,
        "dexterity": 10,
        "constitution": 10,
        "intelligence": 10,
        "wisdom": 10,
        "charisma": 10,
        "proficiencies": [],
    }

    mock_monster_api(monkeypatch, monster_data)

    response = client.post(
        "/api/enemies/import/",
        {"monster_index": "no-hp"},
    )

    assert response.status_code == 200

    monster = Character.objects.get(name="No HP Monster")

    assert monster.max_hp == 1


# Test 12: Import creates combantant card
@pytest.mark.django_db
def test_import_returns_combatant_card(client, monkeypatch):
    monster_data = {
        "name": "Test Dragon",
        "hit_points": 100,
        "armor_class": [{"value": 18}],
        "strength": 20,
        "dexterity": 10,
        "constitution": 18,
        "intelligence": 12,
        "wisdom": 14,
        "charisma": 16,
        "proficiencies": [],
    }

    mock_monster_api(monkeypatch, monster_data)

    response = client.post(
        "/api/enemies/import/",
        {"monster_index": "test-dragon"},
    )

    assert response.status_code == 200
    assert b"Test Dragon" in response.content
    assert b"100" in response.content
