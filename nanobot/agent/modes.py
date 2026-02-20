"""Mode loader and processor for custom prompt injection."""

import json
import re
from pathlib import Path
from typing import Any


class ModeLoader:
    """Load and apply user-defined mode configurations."""

    def __init__(self, workspace: Path):
        self.workspace = workspace
        self.mode_dir = workspace / "mode"

    def get_available_modes(self) -> list[str]:
        """Get list of available mode names."""
        if not self.mode_dir.exists():
            return []
        return [f.stem for f in self.mode_dir.glob("*.json")]

    def load_mode(self, name: str) -> dict[str, Any] | None:
        """Load a specific mode configuration."""
        mode_file = self.mode_dir / f"{name}.json"
        if not mode_file.exists():
            return None
        try:
            return json.loads(mode_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return None

    def apply_mode(self, system_prompt: str, mode_config: dict[str, Any]) -> str:
        """Apply mode configuration to system prompt."""
        result = system_prompt

        regex_rules = mode_config.get("regex_rules", [])
        for rule in regex_rules:
            if isinstance(rule, str) and "->" in rule:
                pattern, replacement = rule.split("->", 1)
                try:
                    result = re.sub(pattern, replacement, result)
                except re.error:
                    pass

        append_content = mode_config.get("append", "")
        if append_content:
            append_content = append_content.replace("\\n", "\n")
            result = f"{result}\n\n{append_content}"

        return result


def parse_mode_command(message: str) -> tuple[str | None, str]:
    """
    Parse mode command from message.
    Returns: (mode_name, remaining_message)
    """
    match = re.match(r"^\s*mode:\s*:\s*(\S+)\s*\n?", message)
    if match:
        mode_name = match.group(1)
        remaining = message[match.end() :].lstrip("\n")
        return mode_name, remaining
    return None, message
