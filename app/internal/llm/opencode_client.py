"""
OpenCode CLI client wrapper for LLM calls.
"""

from __future__ import annotations

import json
import subprocess
from typing import Iterable, List

from app.configs.config import OpenCodeConfig


class OpenCodeClient:
    def __init__(self, config: OpenCodeConfig) -> None:
        self._config = config

    def invoke(self, prompt: str) -> str:
        cmd = self._build_command(prompt)
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=self._config.timeout_seconds,
        )
        if result.returncode != 0:
            raise RuntimeError(
                "OpenCode invocation failed: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )
        output = result.stdout.strip()
        if self._config.format == "json":
            return _extract_text_from_json(output)
        return output

    def _build_command(self, prompt: str) -> List[str]:
        cmd = [self._config.command, "run", prompt, "--model", self._config.model]
        if self._config.variant:
            cmd.extend(["--variant", self._config.variant])
        if self._config.attach_url:
            cmd.extend(["--attach", self._config.attach_url])
        if self._config.format:
            cmd.extend(["--format", self._config.format])
        return cmd


def _extract_text_from_json(output: str) -> str:
    chunks: List[str] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        chunks.extend(_walk_text(payload))
    return "".join(chunks).strip()


def _walk_text(value: object) -> Iterable[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _walk_text(item)]
    if isinstance(value, dict):
        texts: List[str] = []
        if "text" in value and isinstance(value["text"], str):
            texts.append(value["text"])
        for key in ("content", "message", "delta"):
            if key in value:
                texts.extend(_walk_text(value[key]))
        return texts
    return []
