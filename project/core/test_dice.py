from unittest.mock import call, patch

import pytest
from django.test import Client
from django.urls import reverse


@pytest.mark.parametrize("sides", [4, 6, 8, 10, 12, 20])
def test_roll_each_die_keeps_individual_results_and_total(client, sides):
    with patch("core.views.random.randint", side_effect=[1, sides]) as randint:
        response = client.post(reverse("core:roll_dice"), {"sides": sides, "count": 2})

    assert response.status_code == 200
    assert response.json() == {
        "sides": sides,
        "count": 2,
        "rolls": [1, sides],
        "total": 1 + sides,
    }
    assert randint.call_args_list == [call(1, sides), call(1, sides)]


@pytest.mark.parametrize("count", [1, 20])
def test_roll_accepts_minimum_and_maximum_count(client, count):
    with patch("core.views.random.randint", return_value=3) as randint:
        response = client.post(reverse("core:roll_dice"), {"sides": 6, "count": count})

    assert response.status_code == 200
    result = response.json()
    assert result["count"] == count
    assert result["rolls"] == [3] * count
    assert result["total"] == 3 * count
    assert randint.call_count == count


@pytest.mark.parametrize(
    "data, field",
    [
        ({"sides": 3, "count": 1}, "sides"),
        ({"sides": "six", "count": 1}, "sides"),
        ({"sides": "6.5", "count": 1}, "sides"),
        ({"sides": 6, "count": 0}, "count"),
        ({"sides": 6, "count": 21}, "count"),
        ({"sides": 6, "count": "two"}, "count"),
        ({"sides": 6, "count": "1.5"}, "count"),
        ({"count": 1}, "sides"),
        ({"sides": 6}, "count"),
    ],
)
def test_invalid_dice_input_does_not_roll(client, data, field):
    with patch("core.views.random.randint") as randint:
        response = client.post(reverse("core:roll_dice"), data)

    assert response.status_code == 400
    assert field in response.json()
    randint.assert_not_called()


def test_dice_roll_requires_post(client):
    response = client.get(reverse("core:roll_dice"))

    assert response.status_code == 405


@pytest.mark.django_db
def test_home_includes_dice_form(client):
    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert not response.context["dice_form"].is_bound
    assert b'name="sides"' in response.content
    assert b'name="count"' in response.content


@pytest.mark.django_db
def test_dice_roll_requires_csrf_token():
    client = Client(enforce_csrf_checks=True)
    url = reverse("core:roll_dice")
    data = {"sides": 6, "count": 1}

    assert client.post(url, data).status_code == 403

    client.get(reverse("core:home"))
    token = client.cookies["csrftoken"].value
    with patch("core.views.random.randint", return_value=4):
        response = client.post(url, data, HTTP_X_CSRFTOKEN=token)

    assert response.status_code == 200
    assert response.json()["rolls"] == [4]
