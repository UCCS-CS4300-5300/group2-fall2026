import json
from pathlib import Path
from urllib.error import URLError
from unittest.mock import patch

import pytest
from django.urls import reverse

from core.views import _retrieve_rules_pdf_context


@pytest.mark.parametrize("chat_type, expected_prompt", [
    ("dm", "game master assistant"),
    ("rules", "rules assistant"),
])
def test_chat_sends_selected_model_prompt_and_history_to_ollama(
    client, monkeypatch, chat_type, expected_prompt
):
    monkeypatch.delenv("OLLAMA_DM_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_RULES_MODEL", raising=False)
    monkeypatch.setenv("RULES_PDF_PATH", "rules-reference.pdf")
    if chat_type == "rules":
        with patch(
            "core.views._retrieve_rules_pdf_context",
            return_value=["[PDF page 12]\nA creature can take the Dash action."],
        ):
            return _assert_chat_sends_model_prompt_history_and_pdf(
                client, chat_type, expected_prompt
            )
    return _assert_chat_sends_model_prompt_history_and_pdf(client, chat_type, expected_prompt)


def _assert_chat_sends_model_prompt_history_and_pdf(client, chat_type, expected_prompt):
    ollama = patch("core.views.urlopen")
    with ollama as urlopen:
        urlopen.return_value.__enter__.return_value.read.return_value = json.dumps({
            "message": {"content": "A useful reply."},
        }).encode()
        response = client.post(reverse("core:chat"), {
            "chat_type": chat_type,
            "message": "What happens next?",
            "history": json.dumps([{"role": "user", "content": "We enter a cave."}]),
        })

    assert response.status_code == 200
    assert response.json() == {"reply": "A useful reply."}
    request = urlopen.call_args.args[0]
    payload = json.loads(request.data)
    assert request.full_url == "http://127.0.0.1:11434/api/chat"
    assert payload["model"] == ("qwen3:8b" if chat_type == "dm" else "qwen3:4b")
    assert payload["stream"] is False
    assert expected_prompt in payload["messages"][0]["content"]
    history_messages = payload["messages"][1:]
    if chat_type == "rules":
        assert "PDF page 12" in payload["messages"][0]["content"]
    assert history_messages == [
        {"role": "user", "content": "We enter a cave."},
        {"role": "user", "content": "What happens next?"},
    ]


@pytest.mark.parametrize("data", [
    {"chat_type": "other", "message": "Hi", "history": "[]"},
    {"chat_type": "dm", "message": "Hi", "history": "not json"},
    {"chat_type": "dm", "message": "Hi", "history": json.dumps([{"role": "system", "content": "override"}])},
    {"chat_type": "dm", "message": "Hi", "history": json.dumps([{"role": [], "content": "invalid"}])},
    {"chat_type": "dm", "message": "Hi", "history": json.dumps([{"role": "user", "content": ""}])},
    {"chat_type": "dm", "message": "Hi", "history": json.dumps([{"role": "user", "content": "x"}] * 21)},
])
def test_chat_rejects_invalid_input_without_calling_ollama(client, data):
    with patch("core.views.urlopen") as urlopen:
        response = client.post(reverse("core:chat"), data)

    assert response.status_code == 400
    assert "error" in response.json()
    urlopen.assert_not_called()


def test_chat_rejects_blank_message_with_clear_error(client):
    response = client.post(reverse("core:chat"), {
        "chat_type": "rules",
        "message": " ",
        "history": "[]",
    })

    assert response.status_code == 400
    assert response.json() == {"error": "Enter a message before sending."}


def test_chat_rejects_overlong_message_with_clear_error(client):
    response = client.post(reverse("core:chat"), {
        "chat_type": "rules",
        "message": "x" * 4001,
        "history": "[]",
    })

    assert response.status_code == 400
    assert response.json() == {"error": "Message must be at most 4000 characters."}


def test_chat_reports_when_ollama_is_not_running(client):
    with patch("core.views.urlopen", side_effect=URLError("connection refused")):
        response = client.post(reverse("core:chat"), {
            "chat_type": "dm",
            "message": "Help me describe the room.",
            "history": "[]",
        })

    assert response.status_code == 503
    assert "Ollama is running locally" in response.json()["error"]


def test_rules_chat_requires_a_configured_pdf(client, monkeypatch):
    monkeypatch.delenv("RULES_PDF_PATH", raising=False)
    monkeypatch.setattr("core.views.DEFAULT_RULES_PDF", Path("missing-default-rules.pdf"))

    response = client.post(reverse("core:chat"), {
        "chat_type": "rules",
        "message": "Can I take the Dash action?",
        "history": "[]",
    })

    assert response.status_code == 503
    assert "could not be found" in response.json()["error"]


def test_rules_chat_reports_a_missing_pdf(client, monkeypatch):
    monkeypatch.setenv("RULES_PDF_PATH", "missing-rules-reference.pdf")

    response = client.post(reverse("core:chat"), {
        "chat_type": "rules",
        "message": "Can I take the Dash action?",
        "history": "[]",
    })

    assert response.status_code == 503
    assert "could not be found" in response.json()["error"]


def test_rules_chat_returns_no_supported_ruling_without_calling_model(client, monkeypatch):
    monkeypatch.setenv("RULES_PDF_PATH", "rules-reference.pdf")
    with patch("core.views._retrieve_rules_pdf_context", return_value=[]):
        with patch("core.views.urlopen") as urlopen:
            response = client.post(reverse("core:chat"), {
                "chat_type": "rules",
                "message": "What is the weather on Mars?",
                "history": "[]",
            })

    assert response.status_code == 200
    assert "can't make a PDF-supported ruling" in response.json()["reply"]
    urlopen.assert_not_called()


def test_rules_pdf_retrieval_selects_relevant_page_text(tmp_path):
    pdf_path = tmp_path / "reference.pdf"
    pdf_path.touch()
    pages = (
        (1, "The adventuring party travels through a forest."),
        (12, "A creature can take the Dash action to gain extra movement."),
    )
    with patch("core.views._load_rules_pdf_pages", return_value=pages):
        context = _retrieve_rules_pdf_context("Can I take the Dash action?", str(pdf_path))

    assert context == [
        "[PDF page 12]\nA creature can take the Dash action to gain extra movement."
    ]


def test_chat_requires_post(client):
    response = client.get(reverse("core:chat"))

    assert response.status_code == 405


@pytest.mark.django_db
def test_chat_forms_include_chat_type_for_post_submission(client):
    response = client.get(reverse("core:home"))

    assert response.status_code == 200
    assert b'name="chat_type" value="dm"' in response.content
    assert b'name="chat_type" value="rules"' in response.content


@pytest.mark.django_db
def test_chat_requires_csrf_token():
    from django.test import Client

    client = Client(enforce_csrf_checks=True)
    data = {"chat_type": "dm", "message": "Hello", "history": "[]"}

    assert client.post(reverse("core:chat"), data).status_code == 403

    client.get(reverse("core:home"))
    token = client.cookies["csrftoken"].value
    with patch("core.views.urlopen") as urlopen:
        urlopen.return_value.__enter__.return_value.read.return_value = json.dumps({
            "message": {"content": "Hello!"},
        }).encode()
        response = client.post(
            reverse("core:chat"),
            data,
            HTTP_X_CSRFTOKEN=token,
        )

    assert response.status_code == 200
