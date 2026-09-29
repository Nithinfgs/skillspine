"""CommonMark references, without executing or rendering source content."""

import re
from urllib.parse import unquote, urlsplit

from markdown_it import MarkdownIt

from .models import Reference

_CODE_PATH = re.compile(r"^(?:\.{1,2}/|references/|scripts/|assets/)[^\n<>*{}|]+$")


def references(text: str, code_paths: bool = False) -> tuple[list[Reference], int]:
    lines = text.splitlines(keepends=True)
    # YAML metadata is not Markdown. Preserve line numbers without parsing YAML.
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() in {"---", "..."}:
                lines[: i + 1] = ["\n"] * (i + 1)
                break
    parser = MarkdownIt("commonmark", {"html": False})
    result: list[Reference] = []
    external = 0
    for token in parser.parse("".join(lines)):
        if token.type != "inline":
            continue
        line = token.map[0] + 1 if token.map else 1
        for child in token.children or []:
            raw = None
            kind = "link"
            if child.type == "link_open":
                raw = child.attrGet("href")
            elif child.type == "image":
                raw = child.attrGet("src")
                kind = "image"
            elif code_paths and child.type == "code_inline" and _CODE_PATH.fullmatch(child.content):
                raw = child.content
                kind = "code"
            if not isinstance(raw, str):
                continue
            # Windows drive paths must be reported, not mistaken for URL schemes.
            if re.match(r"^[a-zA-Z]:[/\\]", raw):
                result.append(Reference(raw, line, kind))
                continue
            try:
                url = urlsplit(raw)
            except ValueError:
                result.append(Reference(raw, line, kind))
                continue
            if url.scheme or url.netloc:
                external += 1
                continue
            target = unquote(url.path)
            if target:
                result.append(Reference(target, line, kind))
    return result, external
