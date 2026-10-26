"""Structured (JSON) generation with Pydantic validation and bounded repair."""

from __future__ import annotations

import json
import logging
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from tutor.llm.base import CancelToken, ChatMessage, GenerationParams, LLMProvider, StructuredOutputError

log = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)

_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.S)


def extract_json(text: str) -> dict:
    """Find the first JSON object in ``text`` (tolerates code fences and chatter)."""
    text = text.strip()
    if not text:
        raise ValueError("empty response")
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    for m in _FENCE.finditer(text):
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    # balanced-brace scan
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        obj = json.loads(text[start : i + 1])
                        if isinstance(obj, dict):
                            return obj
                    except json.JSONDecodeError:
                        break
                    break
        start = text.find("{", start + 1)
    raise ValueError("no JSON object found")


def _compact_schema(model: type[BaseModel]) -> str:
    return json.dumps(model.model_json_schema(), separators=(",", ":"))


def generate_structured(
    provider: LLMProvider,
    messages: list[ChatMessage],
    model: type[T],
    params: GenerationParams,
    cancel: CancelToken | None = None,
    max_repairs: int = 1,
) -> T:
    """Ask for JSON matching ``model``; validate; at most ``max_repairs`` repair rounds (never endless)."""
    schema = model.model_json_schema()
    instruction = (
        "Respond ONLY with a single JSON object that conforms to this JSON schema "
        "(no markdown, no commentary):\n" + _compact_schema(model)
    )
    msgs = list(messages)
    if msgs and msgs[0].role == "system":
        msgs[0] = ChatMessage("system", msgs[0].content + "\n\n" + instruction)
    else:
        msgs.insert(0, ChatMessage("system", instruction))

    last_error = ""
    for attempt in range(max_repairs + 1):
        raw = provider.complete_json(msgs, schema, params, cancel)
        try:
            data = extract_json(raw)
            return model.model_validate(data)
        except (ValueError, ValidationError) as exc:
            last_error = str(exc)[:800]
            log.info("Structured output invalid (attempt %d): %s", attempt + 1, type(exc).__name__)
            msgs = msgs + [
                ChatMessage("assistant", raw[:4000]),
                ChatMessage(
                    "user",
                    "Your previous reply was not valid for the required JSON schema. Error:\n"
                    f"{last_error}\nReturn the corrected JSON object only.",
                ),
            ]
    raise StructuredOutputError(
        last_error, "The AI model returned malformed structured data. Try again, or choose a more capable model."
    )
