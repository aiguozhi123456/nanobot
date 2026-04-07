"""Tests for the Dream class — two-phase memory consolidation via AgentRunner."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from nanobot.agent.memory import Dream, MemoryStore
from nanobot.agent.runner import AgentRunResult


@pytest.fixture
def store(tmp_path):
    s = MemoryStore(tmp_path)
    s.write_soul("# Soul\n- Helpful")
    s.write_user("# User\n- Developer")
    s.write_memory("# Memory\n- Project X active")
    return s


@pytest.fixture
def mock_provider():
    p = MagicMock()
    p.chat_with_retry = AsyncMock()
    return p


@pytest.fixture
def mock_runner():
    return MagicMock()


@pytest.fixture
def dream(store, mock_provider, mock_runner):
    d = Dream(store=store, provider=mock_provider, model="test-model", max_batch_size=5)
    d._runner = mock_runner
    return d


def _make_run_result(
    stop_reason="completed",
    final_content=None,
    tool_events=None,
    usage=None,
):
    return AgentRunResult(
        final_content=final_content or stop_reason,
        stop_reason=stop_reason,
        messages=[],
        tools_used=[],
        usage={},
        tool_events=tool_events or [],
    )


class TestDreamRun:
    async def test_noop_when_no_unprocessed_history(self, dream, mock_provider, mock_runner, store):
        """Dream should not call LLM when there's nothing to process."""
        result = await dream.run()
        assert result is False
        mock_provider.chat_with_retry.assert_not_called()
        mock_runner.run.assert_not_called()

    async def test_calls_runner_for_unprocessed_entries(
        self, dream, mock_provider, mock_runner, store
    ):
        """Dream should call AgentRunner when there are unprocessed history entries."""
        store.append_history("User prefers dark mode")
        mock_provider.chat_with_retry.return_value = MagicMock(content="New fact")
        mock_runner.run = AsyncMock(
            return_value=_make_run_result(
                tool_events=[{"name": "edit_file", "status": "ok", "detail": "memory/MEMORY.md"}],
            )
        )
        result = await dream.run()
        assert result is True
        mock_runner.run.assert_called_once()
        spec = mock_runner.run.call_args[0][0]
        assert spec.max_iterations == 10
        assert spec.fail_on_tool_error is False

    async def test_advances_dream_cursor(self, dream, mock_provider, mock_runner, store):
        """Dream should advance the cursor after processing."""
        store.append_history("event 1")
        store.append_history("event 2")
        mock_provider.chat_with_retry.return_value = MagicMock(content="Nothing new")
        mock_runner.run = AsyncMock(return_value=_make_run_result())
        await dream.run()
        assert store.get_last_dream_cursor() == 2

    async def test_compacts_processed_history(self, dream, mock_provider, mock_runner, store):
        """Dream should compact history after processing."""
        store.append_history("event 1")
        store.append_history("event 2")
        store.append_history("event 3")
        mock_provider.chat_with_retry.return_value = MagicMock(content="Nothing new")
        mock_runner.run = AsyncMock(return_value=_make_run_result())
        await dream.run()
        # After Dream, cursor is advanced and 3, compact keeps last max_history_entries
        entries = store.read_unprocessed_history(since_cursor=0)
        assert all(e["cursor"] > 0 for e in entries)


class TestDreamKeywordMemory:
    async def test_phase1_receives_keyword_summary(self, dream, mock_provider, mock_runner, store):
        mock_provider.chat_with_retry.return_value = MagicMock(content="[SKIP]")
        mock_runner.run = AsyncMock(return_value=_make_run_result())
        (store.memory_dir / "keyword_memory.json").write_text(
            json.dumps([{"keywords": ["deploy"], "prompt": "Test policy."}])
        )
        store.append_history("User deploys to production")
        await dream.run()
        call_args = mock_provider.chat_with_retry.call_args
        user_msg = call_args.kwargs["messages"][1]["content"]
        assert "keyword_memory.json" in user_msg
        assert "1 rule(s)" in user_msg
        assert "deploy" in user_msg

    async def test_phase2_loads_relevant_keyword_entries(
        self, dream, mock_provider, mock_runner, store
    ):
        (store.memory_dir / "keyword_memory.json").write_text(
            json.dumps(
                [
                    {"keywords": ["deploy"], "prompt": "Blue-green only."},
                    {"keywords": ["database"], "prompt": "Always backup."},
                ]
            )
        )
        store.append_history("User wants canary deployment")
        mock_provider.chat_with_retry.return_value = MagicMock(
            content="[KEYWORD] deploy rule outdated — user prefers canary"
        )
        mock_runner.run = AsyncMock(return_value=_make_run_result())
        await dream.run()
        call_args = mock_runner.run.call_args[0][0]
        user_msg = call_args.initial_messages[1]["content"]
        assert "deploy" in user_msg
        assert "Blue-green" in user_msg

    async def test_phase2_skips_keyword_when_no_findings(
        self, dream, mock_provider, mock_runner, store
    ):
        (store.memory_dir / "keyword_memory.json").write_text(
            json.dumps([{"keywords": ["deploy"], "prompt": "Test policy."}])
        )
        store.append_history("User likes cats")
        mock_provider.chat_with_retry.return_value = MagicMock(
            content="[USER] has a cat named Luna"
        )
        mock_runner.run = AsyncMock(return_value=_make_run_result())
        await dream.run()
        call_args = mock_runner.run.call_args[0][0]
        user_msg = call_args.initial_messages[1]["content"]
        assert "Relevant keyword" not in user_msg

    async def test_phase2_includes_tail_for_new_entries(
        self, dream, mock_provider, mock_runner, store
    ):
        (store.memory_dir / "keyword_memory.json").write_text(
            json.dumps([{"keywords": ["deploy"], "prompt": "Use canary."}])
        )
        store.append_history("User needs docker rule")
        mock_provider.chat_with_retry.return_value = MagicMock(
            content="[KEYWORD] suggest new rule for docker/registry"
        )
        mock_runner.run = AsyncMock(return_value=_make_run_result())
        await dream.run()
        call_args = mock_runner.run.call_args[0][0]
        user_msg = call_args.initial_messages[1]["content"]
        assert "tail" in user_msg.lower()

    def test_git_tracks_keyword_memory(self, tmp_path):
        store = MemoryStore(tmp_path)
        assert "memory/keyword_memory.json" in store.git._tracked_files
