"""Interface and content language (English / Czech).

English is the source language; Czech is layered on top of it:

* ``t(text, **fmt)`` translates an interface string through the catalog in ``ui_cs``.
  Strings without a translation fall back to English, so a missing entry never breaks a page.
* ``apply_language(lang)`` overlays the translated text fields (titles, explanations, options,
  hints ...) onto the shared content objects - lessons, questions, exercises, cases, capstones -
  and restores the English originals when switching back. Ids, code, solutions, datasets and
  grading logic are never touched, so scores and progress are identical in both languages.

The module has no Streamlit dependency, so tests and back-end code can use ``t`` as well.
"""

from __future__ import annotations

import ast
from dataclasses import is_dataclass
from typing import Any

LANGUAGES = {"en": "English", "cs": "Čeština"}
DEFAULT_LANG = "en"

_lang = DEFAULT_LANG
_catalog: dict[str, str] | None = None
# (id(container), field) -> (container, field, original value); restored on switch back to English.
_originals: dict[tuple[int, Any], tuple[Any, Any, Any]] = {}


def get_lang() -> str:
    return _lang


def _ui_catalog() -> dict[str, str]:
    global _catalog
    if _catalog is None:
        from analytics_lab.i18n.ui_cs import UI, long_texts

        from analytics_lab.i18n.content_cs import topics

        # Question topics are stored in the progress database in English, so they are translated at display time.
        _catalog = {**UI, **long_texts(), **topics()}
    return _catalog


def t(text: str, /, **fmt: Any) -> str:
    """Translate an interface string; ``fmt`` values are substituted with ``str.format``."""
    out = _ui_catalog().get(text, text) if _lang == "cs" else text
    return out.format(**fmt) if fmt else out


def tr(value: Any) -> Any:
    """``t`` for display values that may not be strings (dataframe cells, options)."""
    return t(value) if isinstance(value, str) else value


# --------------------------------------------------------------------------- #
# Content overlays                                                             #
# --------------------------------------------------------------------------- #
def _remember(container: Any, key: Any) -> None:
    k = (id(container), key)
    if k not in _originals:
        value = container[key] if isinstance(container, (dict, list)) else getattr(container, key)
        _originals[k] = (container, key, value)


def _assign(container: Any, key: Any, value: Any) -> None:
    _remember(container, key)
    if isinstance(container, (dict, list)):
        container[key] = value
    else:
        object.__setattr__(container, key, value)  # also works for frozen dataclasses


def overlay(obj: Any, patch: dict[str, Any]) -> None:
    """Apply translated fields to a dataclass in place.

    * ``{"field": "text"}`` replaces a field (lists of strings are replaced whole).
    * ``{"field": {...}}`` recurses into a nested dataclass (e.g. ``worked_example``).
    * ``{"field": [{...}, ...]}`` or ``[("text", "why"), ...]`` patches a list of dataclasses
      element by element; the lengths must match so option order (and therefore grading) is preserved.
    """
    for name, val in patch.items():
        if name == "msgs":  # translated assert messages inside hidden check code
            _assign(obj, "code", replace_assert_messages(obj.code, val))
            continue
        if not hasattr(obj, name):
            raise KeyError(f"{type(obj).__name__} has no field {name!r}")
        cur = getattr(obj, name)
        if isinstance(val, dict) and is_dataclass(cur):
            overlay(cur, val)
        elif isinstance(val, list) and cur and is_dataclass(cur[0]):
            if len(val) != len(cur):
                raise ValueError(f"{type(obj).__name__}.{name}: {len(val)} translations for {len(cur)} items")
            for item, p in zip(cur, val):
                if isinstance(p, (tuple, list)):
                    p = dict(zip(_TUPLE_FIELDS[type(item).__name__], p))
                overlay(item, p)
        else:
            if isinstance(cur, list) and isinstance(val, list) and len(cur) != len(val) and name in _SAME_LENGTH:
                raise ValueError(f"{type(obj).__name__}.{name}: {len(val)} translations for {len(cur)} items")
            _assign(obj, name, val)


def assert_messages(code: str) -> list[str]:
    """Source text of every ``assert ..., <message>`` in a check, in source order."""
    tree = ast.parse(code)
    nodes = sorted((n.msg for n in ast.walk(tree) if isinstance(n, ast.Assert) and n.msg is not None), key=lambda m: (m.lineno, m.col_offset))
    return [ast.get_source_segment(code, m) for m in nodes]


def replace_assert_messages(code: str, messages: list[str | None]) -> str:
    """Swap assert messages (given as Python expression source, ``None`` = keep) without touching the check logic."""
    tree = ast.parse(code)
    nodes = sorted((n.msg for n in ast.walk(tree) if isinstance(n, ast.Assert) and n.msg is not None), key=lambda m: (m.lineno, m.col_offset))
    if len(nodes) != len(messages):
        raise ValueError(f"{len(messages)} translated messages for {len(nodes)} asserts in check code")
    # AST offsets are UTF-8 byte offsets, so splice on bytes.
    raw = code.encode("utf-8")
    starts = [0]
    for line in raw.splitlines(keepends=True):
        starts.append(starts[-1] + len(line))
    for node, new in sorted(zip(nodes, messages), key=lambda p: (p[0].lineno, p[0].col_offset), reverse=True):
        if new is None:
            continue
        a = starts[node.lineno - 1] + node.col_offset
        b = starts[node.end_lineno - 1] + node.end_col_offset
        raw = raw[:a] + new.encode("utf-8") + raw[b:]
    out = raw.decode("utf-8")
    ast.parse(out)  # the translated check must still be valid Python
    return out


def overlay_dict(target: dict, patch: dict) -> None:
    for k, v in patch.items():
        if k not in target:
            raise KeyError(k)
        _assign(target, k, v)


def overlay_list(target: list, values: list) -> None:
    if len(values) != len(target):
        raise ValueError(f"{len(values)} translations for {len(target)} items")
    for i, v in enumerate(values):
        _assign(target, i, v)


# Positional shorthand for small dataclasses, e.g. options as ("text", "why").
_TUPLE_FIELDS = {
    "Option": ("text", "why"),
    "Check": ("name", "hint"),
    "CaseObjective": ("prompt", "options", "explanation"),
    "RubricCriterion": ("name", "description", "levels", "indicators"),
    "Milestone": ("title", "description", "checklist"),
    "WorkedExample": ("explanation",),
}
# Lists whose positions carry meaning (answer keys, check order) and must keep their length.
_SAME_LENGTH = {"options", "levels", "checklist", "rubric", "hints"}


def _restore() -> None:
    for container, key, value in reversed(list(_originals.values())):
        if isinstance(container, (dict, list)):
            container[key] = value
        else:
            object.__setattr__(container, key, value)
    _originals.clear()


def apply_language(lang: str) -> None:
    """Switch the interface and all learning content to ``lang`` ("en" or "cs")."""
    global _lang
    lang = lang if lang in LANGUAGES else DEFAULT_LANG
    if lang == _lang:
        return
    _restore()
    if lang == "cs":
        from analytics_lab.i18n.content_cs import apply_all

        apply_all()
    _lang = lang
