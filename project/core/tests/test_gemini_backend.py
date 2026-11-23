import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest

from core.ai import gemini_backend as svc
from core.ai.ai_exceptions import ChatError

def fake_response(text):
    return SimpleNamespace(text=text)


def fake_embedding(values):
    return SimpleNamespace(embeddings=[SimpleNamespace(values=values)])


@pytest.fixture
def mock_client(monkeypatch):
    client = MagicMock()
    monkeypatch.setattr(svc, "client", client)
    return client


_REAL_GET_DATA = svc.get_data


@pytest.fixture(autouse=True)
def clear_data_cache():
    _REAL_GET_DATA.cache_clear()
    yield
    _REAL_GET_DATA.cache_clear()

class TestBuildContents:
    def test_no_history_no_context_is_single_user_message(self):
        contents = svc.build_contents("Hello", [], None)
        assert len(contents) == 1
        assert contents[0].role == "user"
        assert contents[0].parts[0].text == "Hello"

    def test_maps_assistant_role_to_model(self):
        history = [
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
        ]
        contents = svc.build_contents("Next", history, None)
        assert [c.role for c in contents] == ["user", "model", "user"]

    def test_drops_leading_assistant_messages(self):
        history = [
            {"role": "assistant", "content": "Stray greeting"},
            {"role": "user", "content": "Question"},
            {"role": "assistant", "content": "Answer"},
        ]
        contents = svc.build_contents("Follow-up", history, None)
        assert contents[0].role == "user"
        assert contents[0].parts[0].text == "Question"

    def test_filters_out_unknown_roles(self):
        history = [
            {"role": "system", "content": "ignore me"},
            {"role": "user", "content": "Hi"},
        ]
        contents = svc.build_contents("Next", history, None)
        texts = [c.parts[0].text for c in contents]
        assert "ignore me" not in texts

    def test_history_of_only_assistant_messages_is_dropped_entirely(self):
        history = [{"role": "assistant", "content": "Hello"}]
        contents = svc.build_contents("Hi", history, None)
        assert len(contents) == 1
        assert contents[0].role == "user"

    def test_rules_context_is_included_in_final_message(self):
        ctx = ["Grappling: use Athletics.", "Opportunity attacks: use reaction."]
        contents = svc.build_contents("How does grappling work?", [], ctx)
        final = contents[-1]
        assert final.role == "user"
        text = final.parts[0].text
        assert "Rules excerpts:" in text
        assert "Grappling: use Athletics." in text
        assert "Question: How does grappling work?" in text

    def test_empty_rules_context_is_treated_as_no_context(self):
        contents = svc.build_contents("Just a message", [], [])
        assert contents[-1].parts[0].text == "Just a message"

    def test_last_message_is_always_the_new_user_message(self):
        history = [
            {"role": "user", "content": "a"},
            {"role": "assistant", "content": "b"},
        ]
        contents = svc.build_contents("c", history, None)
        assert contents[-1].role == "user"
        assert contents[-1].parts[0].text == "c"

class TestGetAiReply:
    def test_returns_response_text(self, mock_client):
        mock_client.models.generate_content.return_value = fake_response("A goblin.")
        reply = svc.get_ai_reply("Describe a monster", "sys prompt", [], None)
        assert reply == "A goblin."

    def test_passes_model_prompt_and_generation_settings(self, mock_client):
        mock_client.models.generate_content.return_value = fake_response("ok")
        svc.get_ai_reply("msg", "my system prompt", [], None, output_tokens=123, temp=0.5)

        kwargs = mock_client.models.generate_content.call_args.kwargs
        assert kwargs["model"] == svc.CHAT_MODEL
        assert kwargs["config"].system_instruction == "my system prompt"
        assert kwargs["config"].max_output_tokens == 123
        assert kwargs["config"].temperature == 0.5

    def test_api_failure_becomes_chat_error_503(self, mock_client):
        mock_client.models.generate_content.side_effect = RuntimeError("boom")
        with pytest.raises(ChatError) as exc:
            svc.get_ai_reply("msg", "sys", [], None)
        assert exc.value.status == 503
        assert "boom" in str(exc.value)

class TestRewriteQuery:
    def test_no_history_skips_api_call(self, mock_client):
        result = svc.rewrite_query("How does grappling work?", [])
        assert result == "How does grappling work?"
        mock_client.models.generate_content.assert_not_called()

    def test_returns_stripped_rewrite(self, mock_client):
        mock_client.models.generate_content.return_value = fake_response(
            "  How does grappling work?  \n"
        )
        history = [{"role": "user", "content": "Tell me about grappling"}]
        assert svc.rewrite_query("how does it work?", history) == "How does grappling work?"

    def test_empty_rewrite_falls_back_to_original_message(self, mock_client):
        mock_client.models.generate_content.return_value = fake_response("   ")
        history = [{"role": "user", "content": "hi"}]
        assert svc.rewrite_query("original", history) == "original"

    def test_prompt_contains_transcript_and_latest_message(self, mock_client):
        mock_client.models.generate_content.return_value = fake_response("x")
        history = [
            {"role": "user", "content": "What is grappling?"},
            {"role": "assistant", "content": "A special melee attack."},
        ]
        svc.rewrite_query("How do I escape it?", history)

        prompt = mock_client.models.generate_content.call_args.kwargs["contents"]
        assert "user: What is grappling?" in prompt
        assert "model: A special melee attack." in prompt
        assert "Latest message: How do I escape it?" in prompt

    def test_uses_deterministic_low_token_config(self, mock_client):
        mock_client.models.generate_content.return_value = fake_response("x")
        svc.rewrite_query("q", [{"role": "user", "content": "h"}])
        config = mock_client.models.generate_content.call_args.kwargs["config"]
        assert config.temperature == 0.0
        assert config.max_output_tokens == 100

    def test_api_failure_becomes_chat_error_503(self, mock_client):
        mock_client.models.generate_content.side_effect = RuntimeError("down")
        with pytest.raises(ChatError) as exc:
            svc.rewrite_query("q", [{"role": "user", "content": "h"}])
        assert exc.value.status == 503

class TestGetQuestionVector:
    def test_returns_unit_vector(self, mock_client):
        mock_client.models.embed_content.return_value = fake_embedding([3.0, 4.0])
        vec = svc.get_question_vector("anything")
        assert vec.dtype == np.float32
        assert np.linalg.norm(vec) == pytest.approx(1.0)
        np.testing.assert_allclose(vec, [0.6, 0.8], rtol=1e-5)

    def test_uses_retrieval_query_task_and_embedding_model(self, mock_client):
        mock_client.models.embed_content.return_value = fake_embedding([1.0, 0.0])
        svc.get_question_vector("q")
        kwargs = mock_client.models.embed_content.call_args.kwargs
        assert kwargs["model"] == svc.EMBEDDING_MODEL
        assert kwargs["contents"] == "q"
        assert kwargs["config"].task_type == "RETRIEVAL_QUERY"

    def test_api_failure_becomes_chat_error_503(self, mock_client):
        mock_client.models.embed_content.side_effect = RuntimeError("nope")
        with pytest.raises(ChatError) as exc:
            svc.get_question_vector("q")
        assert exc.value.status == 503

@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    vectors = np.array([[3.0, 4.0], [0.0, 2.0]], dtype=np.float64)
    np.save(tmp_path / "embeddings_partial.npy", vectors)
    chunks = ["chunk about fire", "chunk about ice"]
    (tmp_path / "chunks.json").write_text(json.dumps(chunks), encoding="utf-8")
    monkeypatch.setattr(svc, "DATA_DIR", tmp_path)
    return tmp_path


class TestGetData:
    def test_loads_chunks_and_normalizes_rows(self, data_dir):
        chunks, matrix = svc.get_data()
        assert chunks == ["chunk about fire", "chunk about ice"]
        assert matrix.dtype == np.float32
        np.testing.assert_allclose(np.linalg.norm(matrix, axis=1), [1.0, 1.0], rtol=1e-5)
        np.testing.assert_allclose(matrix[0], [0.6, 0.8], rtol=1e-5)

    def test_result_is_cached(self, data_dir):
        first = svc.get_data()
        second = svc.get_data()
        assert first[0] is second[0]
        assert first[1] is second[1]

    def test_missing_files_raise(self, tmp_path, monkeypatch):
        monkeypatch.setattr(svc, "DATA_DIR", tmp_path)
        with pytest.raises(FileNotFoundError):
            svc.get_data()

class TestGetRulesContext:
    @pytest.fixture
    def fake_data(self, monkeypatch):
        chunks = ["east", "north", "northeast"]
        matrix = np.array(
            [[1.0, 0.0], [0.0, 1.0], [0.7071, 0.7071]], dtype=np.float32
        )
        monkeypatch.setattr(svc, "get_data", lambda: (chunks, matrix))
        monkeypatch.setattr(svc, "rewrite_query", lambda m, h: m)
        return chunks, matrix

    def test_returns_most_similar_chunks_first(self, fake_data, monkeypatch):
        monkeypatch.setattr(
            svc, "get_question_vector", lambda m: np.array([1.0, 0.0], dtype=np.float32)
        )
        result = svc.get_rules_context("q", [], size=3)
        assert result == ["east", "northeast", "north"]

    def test_respects_size_limit(self, fake_data, monkeypatch):
        monkeypatch.setattr(
            svc, "get_question_vector", lambda m: np.array([0.0, 1.0], dtype=np.float32)
        )
        result = svc.get_rules_context("q", [], size=1)
        assert result == ["north"]

    def test_size_larger_than_data_returns_everything(self, fake_data, monkeypatch):
        monkeypatch.setattr(
            svc, "get_question_vector", lambda m: np.array([1.0, 0.0], dtype=np.float32)
        )
        assert len(svc.get_rules_context("q", [], size=50)) == 3

    def test_embeds_the_rewritten_query_not_the_raw_message(self, fake_data, monkeypatch):
        monkeypatch.setattr(svc, "rewrite_query", lambda m, h: "REWRITTEN")
        embed = MagicMock(return_value=np.array([1.0, 0.0], dtype=np.float32))
        monkeypatch.setattr(svc, "get_question_vector", embed)
        svc.get_rules_context("raw message", [{"role": "user", "content": "x"}])
        embed.assert_called_once_with("REWRITTEN")

    def test_data_loading_error_propagates(self, monkeypatch):
        def boom():
            raise FileNotFoundError("no embeddings")
        monkeypatch.setattr(svc, "get_data", boom)
        with pytest.raises(FileNotFoundError):
            svc.get_rules_context("q", [])

    def test_embedding_error_propagates(self, fake_data, monkeypatch):
        def boom(m):
            raise ChatError("embed failed", status=503)
        monkeypatch.setattr(svc, "get_question_vector", boom)
        with pytest.raises(ChatError):
            svc.get_rules_context("q", [])

class TestParseChatRequest:
    @pytest.fixture
    def pipeline(self, monkeypatch, mock_client):
        mocks = SimpleNamespace(
            verify=MagicMock(),
            rules=MagicMock(return_value=["excerpt 1", "excerpt 2"]),
            reply=MagicMock(return_value="AI says hi"),
        )
        monkeypatch.setattr(svc, "verify_chat_parameters", mocks.verify)
        monkeypatch.setattr(svc, "get_rules_context", mocks.rules)
        monkeypatch.setattr(svc, "get_ai_reply", mocks.reply)
        return mocks

    def test_missing_api_key_raises_503(self, monkeypatch):
        monkeypatch.setattr(svc, "client", None)
        with pytest.raises(ChatError) as exc:
            svc.parse_chat_request("dm", "hello", [])
        assert exc.value.status == 503
        assert "not configured" in str(exc.value)

    def test_dm_chat_skips_rules_retrieval(self, pipeline):
        reply = svc.parse_chat_request("dm", "Describe a tavern", [])
        assert reply == "AI says hi"
        pipeline.rules.assert_not_called()
        pipeline.reply.assert_called_once_with(
            "Describe a tavern", svc.CHAT_SYSTEM_PROMPTS["dm"], [], None
        )

    def test_rules_chat_retrieves_context_and_passes_it_on(self, pipeline):
        svc.parse_chat_request("rules", "How does grappling work?", [])
        pipeline.rules.assert_called_once()
        args = pipeline.reply.call_args.args
        assert args[1] == svc.CHAT_SYSTEM_PROMPTS["rules"]
        assert args[3] == ["excerpt 1", "excerpt 2"]

    def test_history_is_truncated_to_most_recent_messages(self, pipeline):
        n = svc.MAX_CHAT_HISTORY_MESSAGES + 4
        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"}
            for i in range(n)
        ]
        svc.parse_chat_request("dm", "hi", history)

        passed_history = pipeline.reply.call_args.args[2]
        assert len(passed_history) == svc.MAX_CHAT_HISTORY_MESSAGES
        assert passed_history == history[-svc.MAX_CHAT_HISTORY_MESSAGES:]

    def test_short_history_is_left_alone(self, pipeline):
        history = [{"role": "user", "content": "a"}]
        svc.parse_chat_request("dm", "hi", history)
        assert pipeline.reply.call_args.args[2] == history

    def test_verification_runs_before_any_ai_call(self, pipeline):
        pipeline.verify.side_effect = ChatError("bad input", status=400)
        with pytest.raises(ChatError) as exc:
            svc.parse_chat_request("dm", "hi", [])
        assert exc.value.status == 400
        pipeline.rules.assert_not_called()
        pipeline.reply.assert_not_called()

    def test_verification_receives_truncated_history_and_limits(self, pipeline):
        history = [
            {"role": "user", "content": f"m{i}"}
            for i in range(svc.MAX_CHAT_HISTORY_MESSAGES + 2)
        ]
        svc.parse_chat_request("dm", "hi", history)
        pipeline.verify.assert_called_once_with(
            "dm",
            "hi",
            history[-svc.MAX_CHAT_HISTORY_MESSAGES:],
            svc.CHAT_SYSTEM_PROMPTS,
            svc.MAX_CHAT_MESSAGE_LENGTH,
            svc.MAX_CHAT_HISTORY_MESSAGES,
        )

    def test_ai_reply_error_propagates(self, pipeline):
        pipeline.reply.side_effect = ChatError("gemini down", status=503)
        with pytest.raises(ChatError) as exc:
            svc.parse_chat_request("dm", "hi", [])
        assert exc.value.status == 503

    def test_rules_retrieval_error_propagates_and_skips_reply(self, pipeline):
        pipeline.rules.side_effect = ChatError("embed failed", status=503)
        with pytest.raises(ChatError):
            svc.parse_chat_request("rules", "q", [])
        pipeline.reply.assert_not_called()

class TestEndToEndWithMockedGemini:
    def test_rules_flow_uses_retrieved_chunks_in_prompt(
        self, mock_client, data_dir, monkeypatch
    ):
        monkeypatch.setattr(svc, "verify_chat_parameters", lambda *a, **k: None)

        mock_client.models.embed_content.return_value = fake_embedding([3.0, 4.0])
        mock_client.models.generate_content.return_value = fake_response("Fire is hot.")

        reply = svc.parse_chat_request("rules", "Tell me about fire", [])

        assert reply == "Fire is hot."
        sent = mock_client.models.generate_content.call_args.kwargs["contents"]
        final_text = sent[-1].parts[0].text
        assert "chunk about fire" in final_text
        assert "Question: Tell me about fire" in final_text