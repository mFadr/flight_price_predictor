"""Markdown + LaTeX + code rendering for QTextBrowser (fully offline).

Math between $...$, $$...$$, \\(...\\) or \\[...\\] is rendered to PNG with
matplotlib's mathtext and registered as a document resource. Code blocks get
Pygments syntax highlighting with inline styles. If a formula cannot be
rendered, its source is shown as code - never silently dropped.
"""

from __future__ import annotations

import hashlib
import html
import io
import re

import markdown
from matplotlib import mathtext
from matplotlib.font_manager import FontProperties
from PySide6.QtCore import QUrl
from PySide6.QtGui import QImage, QTextDocument

_MATH = re.compile(r"\$\$(.+?)\$\$|\\\[(.+?)\\\]|\\\((.+?)\\\)|(?<![\\$\w])\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\w)", re.S)
_FENCE = re.compile(r"(```.*?```|`[^`\n]+`)", re.S)
_MD = markdown.Markdown(
    extensions=["fenced_code", "tables", "codehilite", "sane_lists", "nl2br"],
    extension_configs={"codehilite": {"noclasses": True, "pygments_style": "friendly", "guess_lang": False}},
)
# Commands mathtext does not know -> close equivalents
_TEX_FIXES = [(r"\\dfrac", r"\\frac"), (r"\\tfrac", r"\\frac"), (r"\\text\{", r"\\mathrm{"), (r"\\operatorname\{", r"\\mathrm{"),
              (r"\\left", ""), (r"\\right", ""), (r"\\,", r"\\ "), (r"\\;", r"\\ "), (r"\\quad", r"\\ \\ "),
              (r"\\le\b", r"\\leq"), (r"\\ge\b", r"\\geq"), (r"\\implies", r"\\Rightarrow"), (r"\\cdotp", r"\\cdot")]


class MathRenderer:
    def __init__(self, font_size: int = 12):
        self.font_size = font_size
        self._cache: dict[str, QImage | None] = {}

    def image(self, tex: str, display: bool) -> tuple[str, QImage | None]:
        key = hashlib.sha1(f"{display}{self.font_size}{tex}".encode()).hexdigest()[:16]
        if key not in self._cache:
            self._cache[key] = self._render(tex, display)
        return key, self._cache[key]

    def _render(self, tex: str, display: bool) -> QImage | None:
        src = tex.strip()
        for a, b in _TEX_FIXES:
            src = re.sub(a, b, src)
        src = src.replace("\n", " ")
        buf = io.BytesIO()
        try:
            size = self.font_size + (3 if display else 1)
            mathtext.math_to_image(f"${src}$", buf, prop=FontProperties(size=size), dpi=110, format="png")
        except Exception:
            return None
        img = QImage()
        img.loadFromData(buf.getvalue(), "PNG")
        return None if img.isNull() else img


class Renderer:
    def __init__(self, font_size: int = 11):
        self.math = MathRenderer(font_size + 1)

    def to_html(self, text: str, doc: QTextDocument | None) -> str:
        placeholders: dict[str, str] = {}

        def math_sub(segment: str) -> str:
            def repl(m: re.Match) -> str:
                display = m.group(1) is not None or m.group(2) is not None
                tex = next(g for g in m.groups() if g is not None)
                key, img = self.math.image(tex, display)
                token = f"MATHPH{len(placeholders)}X"
                if img is not None and doc is not None:
                    url = QUrl(f"math://{key}")
                    doc.addResource(QTextDocument.ResourceType.ImageResource, url, img)
                    tag = f'<img src="math://{key}" style="vertical-align: middle;">'
                    placeholders[token] = f'<div align="center">{tag}</div>' if display else tag
                else:
                    placeholders[token] = f"<code>{html.escape(tex)}</code>"
                return token
            return _MATH.sub(repl, segment)

        # Only replace math outside code spans/blocks.
        parts = _FENCE.split(text)
        text = "".join(p if i % 2 else math_sub(p) for i, p in enumerate(parts))
        _MD.reset()
        out = _MD.convert(text)
        for token, rep in placeholders.items():
            out = out.replace(token, rep)
        # QTextDocument gives <p> a large default top margin; keep bubbles compact.
        return out.replace("<p>", "<p style='margin-top:4px; margin-bottom:6px'>")


def escape_plain(text: str) -> str:
    return html.escape(text).replace("\n", "<br>")
