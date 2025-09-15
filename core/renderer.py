from __future__ import annotations

import re

try:
    import markdown as _markdown
except Exception:  # pragma: no cover
    _markdown = None

try:
    from pygments.formatters import HtmlFormatter
except Exception:  # pragma: no cover
    HtmlFormatter = None


def _transform_custom_tags(text: str) -> str:
    # {color:<val>}...{/color} -> <span style="color:<val>">...</span>
    def repl_color(m: re.Match) -> str:
        val = m.group(1).strip()
        inner = m.group(2)
        return f"<span style=\"color:{val}\">{inner}</span>"

    # {highlight:<val>}...{/highlight} -> <span style="background:<val>">...</span>
    def repl_highlight(m: re.Match) -> str:
        val = m.group(1).strip()
        inner = m.group(2)
        return f"<span style=\"background:{val}\">{inner}</span>"

    text = re.sub(r"\{color:([^}]+)\}(.*?)\{/color\}", repl_color, text, flags=re.DOTALL)
    text = re.sub(r"\{highlight:([^}]+)\}(.*?)\{/highlight\}", repl_highlight, text, flags=re.DOTALL)
    return text


def render_markdown_html(text: str, css: str) -> str:
    text = _transform_custom_tags(text)
    if not _markdown:
        safe = (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        body = f"<pre>{safe}</pre>"
    else:
        try:
            body = _markdown.markdown(
                text,
                extensions=["extra", "codehilite"],
                extension_configs={
                    'codehilite': {
                        'guess_lang': True,
                        'noclasses': False,
                    }
                }
            )  # tables, fenced code, and highlighted code via Pygments
        except Exception:
            safe = (
                text.replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            body = f"<pre>{safe}</pre>"
    # Simple task list post-processing: turn [ ] / [x] at list starts into checkboxes
    body = re.sub(r"<li>\s*\[ \]\s+", "<li><input type='checkbox' disabled> ", body)
    body = re.sub(r"<li>\s*\[x\]\s+", "<li><input type='checkbox' checked disabled> ", body, flags=re.IGNORECASE)
    return f"<html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"


def pygments_css(dark: bool) -> str:
    if not HtmlFormatter:
        return ""
    style = 'monokai' if dark else 'default'
    try:
        return HtmlFormatter(style=style).get_style_defs('.codehilite')
    except Exception:
        return HtmlFormatter().get_style_defs('.codehilite')
