import json
import pytest
from unittest.mock import patch, MagicMock
from urllib.error import URLError, HTTPError

from django.urls import reverse

def mock_api_response(data):
    """Create a fake API response containing JSON data. """
    response = MagicMock()
    response.__enter__.return_value = response
    response.read.return_value = json.dumps(data).encode("utf-8")
    return response


# Test 1 searching without a query retruns HTTP 400
def test_search_without_query(client):
    response = client.get("/api/enemies/")

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
        "dexerity": 14,
        "constitution": 10,
        "wisdom": 8,
        "charisma": 8,
        "actions": [],
    }

    mock_urlopen.side_effect = [
        mock_api_response(search_results),
        mock_api_response(monster_details),
    ]

    response = client.get("/api/enemies/?q=Goblin")

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
        ("/api/enemies/?q=Goblin")
    )

    assert response.status_code == 200
    assert response.json()["monsters"] == []


# Test 4 A network failure returns HTTP 502
@patch("core.views.urlopen")
def test_api_connection_error_returns_502(mock_urlopen, client):
    mock_urlopen.side_effect = URLError("Connection failed")
    response = client.get("/api/enemies/?q=Goblin")

# Test 5: POST requests not allowed
def test_post_request_is_not_allowed(client):
    response = client.post("/api/enemies/?q=Goblin")
    assert response.status_code == 405

# Test 6: Whitespace only query - confirms .strip() handles blank searches
def test_search_with_whitespace_query(client):
    response = client.get("/api/enemies/?q=%20%20%20")

    assert response.status_code == 200
    assert response.json() == {"monsters": []}

# Test 7: Invalid JSON from the API - tests error handling 
@patch("core.views.urlopen")
def test_invaid_api_json(mock_urlopen, client):
    mock_response = MagicMock()
    mock_response.__enter__.return_value = mock_response
    mock_response.read.return_value = b"not valid json"

    mock_urlopen.return_value = mock_response

    response = client.get("/api/enemies/?q=Goblin")

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

    response = client.get("/api/enemies/?q=Goblin")

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

    response = client.get("/api/enemies/?q=Goblin")

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

    response = client.get("/api/enemies/?q=Monster")

    assert response.status_code == 200
    assert len(response.json()["monsters"]) <= 5