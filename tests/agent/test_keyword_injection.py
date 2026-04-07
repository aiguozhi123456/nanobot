"""Tests for keyword-triggered memory injection."""

from __future__ import annotations

import json
from pathlib import Path

from nanobot.agent.context import ContextBuilder


def _make_workspace(tmp_path: Path, keyword_data: list[dict] | None = None) -> Path:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    if keyword_data is not None:
        mem_dir = workspace / "memory"
        mem_dir.mkdir()
        (mem_dir / "keyword_memory.json").write_text(
            json.dumps(keyword_data, ensure_ascii=False), encoding="utf-8"
        )
    return workspace


def _get_keyword_msg(messages: list[dict]) -> dict | None:
    for msg in messages:
        if msg["role"] == "system" and "## Keyword Memories" in msg.get("content", ""):
            return msg
    return None


def test_keyword_memory_injected_when_keyword_matches(tmp_path):
    data = [
        {"keywords": ["deploy", "发布"], "prompt": "Use blue-green deployment strategy."},
        {"keywords": ["database", "数据库"], "prompt": "Always backup before schema changes."},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    messages = builder.build_messages(
        history=[], current_message="请帮我deploy到生产环境", channel="cli", chat_id="direct"
    )
    kw_msg = _get_keyword_msg(messages)
    assert kw_msg is not None
    assert "blue-green deployment" in kw_msg["content"]
    assert "backup before schema" not in kw_msg["content"]


def test_keyword_memory_injected_multiple_matches(tmp_path):
    data = [
        {"keywords": ["deploy"], "prompt": "Use blue-green deployment."},
        {"keywords": ["database"], "prompt": "Backup before changes."},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    messages = builder.build_messages(
        history=[], current_message="deploy the database changes", channel="cli", chat_id="direct"
    )
    kw_msg = _get_keyword_msg(messages)
    assert kw_msg is not None
    assert "blue-green" in kw_msg["content"]
    assert "Backup before" in kw_msg["content"]


def test_keyword_memory_not_injected_when_no_match(tmp_path):
    data = [
        {"keywords": ["deploy"], "prompt": "Use blue-green deployment."},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    messages = builder.build_messages(
        history=[], current_message="今天天气怎么样", channel="cli", chat_id="direct"
    )
    assert _get_keyword_msg(messages) is None


def test_keyword_memory_not_injected_when_no_message(tmp_path):
    data = [
        {"keywords": ["deploy"], "prompt": "Use blue-green deployment."},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    prompt = builder.build_system_prompt()
    assert "## Keyword Memories" not in prompt


def test_keyword_memory_graceful_when_file_missing(tmp_path):
    workspace = _make_workspace(tmp_path)
    builder = ContextBuilder(workspace)

    messages = builder.build_messages(
        history=[], current_message="deploy something", channel="cli", chat_id="direct"
    )
    assert _get_keyword_msg(messages) is None


def test_keyword_memory_graceful_when_invalid_json(tmp_path):
    workspace = _make_workspace(tmp_path)
    mem_dir = workspace / "memory"
    mem_dir.mkdir()
    (mem_dir / "keyword_memory.json").write_text("not valid json", encoding="utf-8")

    builder = ContextBuilder(workspace)
    messages = builder.build_messages(
        history=[], current_message="deploy something", channel="cli", chat_id="direct"
    )
    assert _get_keyword_msg(messages) is None


def test_keyword_memory_case_insensitive(tmp_path):
    data = [
        {"keywords": ["Deploy"], "prompt": "Use blue-green deployment."},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    messages = builder.build_messages(
        history=[], current_message="DEPLOY now", channel="cli", chat_id="direct"
    )
    kw_msg = _get_keyword_msg(messages)
    assert kw_msg is not None
    assert "blue-green" in kw_msg["content"]


def test_keyword_memory_substring_match(tmp_path):
    data = [
        {"keywords": ["deploy"], "prompt": "Use blue-green deployment."},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    messages = builder.build_messages(
        history=[], current_message="redeploying the service", channel="cli", chat_id="direct"
    )
    kw_msg = _get_keyword_msg(messages)
    assert kw_msg is not None
    assert "blue-green" in kw_msg["content"]


def test_keyword_memory_placed_after_history_before_user_message(tmp_path):
    data = [
        {"keywords": ["deploy"], "prompt": "Use blue-green deployment."},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    messages = builder.build_messages(
        history=[{"role": "user", "content": "hello"}],
        current_message="deploy to production",
        channel="cli",
        chat_id="direct",
    )

    kw_idx = next(
        i for i, m in enumerate(messages) if "## Keyword Memories" in m.get("content", "")
    )
    user_idx = next(
        i
        for i, m in enumerate(messages)
        if m["role"] == "user" and "deploy" in m.get("content", "")
    )

    assert kw_idx > 0, "keyword injection should come after system prompt"
    assert kw_idx < user_idx, "keyword injection should come before current user message"


def test_keyword_memory_does_not_change_system_prompt(tmp_path):
    data = [
        {"keywords": ["deploy"], "prompt": "Use blue-green deployment."},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    prompt_no_keyword = builder.build_system_prompt()

    messages = builder.build_messages(
        history=[], current_message="deploy now", channel="cli", chat_id="direct"
    )
    prompt_with_keyword = messages[0]["content"]

    assert prompt_no_keyword == prompt_with_keyword


def test_keyword_memory_empty_keywords_list(tmp_path):
    data = [
        {"keywords": [], "prompt": "Should not match."},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    messages = builder.build_messages(
        history=[], current_message="anything", channel="cli", chat_id="direct"
    )
    assert _get_keyword_msg(messages) is None


def test_keyword_memory_entry_without_prompt(tmp_path):
    data = [
        {"keywords": ["deploy"]},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    messages = builder.build_messages(
        history=[], current_message="deploy now", channel="cli", chat_id="direct"
    )
    assert _get_keyword_msg(messages) is None


def test_keyword_memory_chinese_keyword_match(tmp_path):
    data = [
        {"keywords": ["数据库"], "prompt": "Always backup before schema changes."},
    ]
    workspace = _make_workspace(tmp_path, data)
    builder = ContextBuilder(workspace)

    messages = builder.build_messages(
        history=[], current_message="请修改数据库表结构", channel="cli", chat_id="direct"
    )
    kw_msg = _get_keyword_msg(messages)
    assert kw_msg is not None
    assert "backup before schema" in kw_msg["content"]
