"""Structured navigation adapters."""

from __future__ import annotations

import re
import urllib.parse
from typing import Any

from .diagnostics import Diagnostic
from .source import byte_offset
from .structured import NavigationEntry, SourceDocument, stable_hash

_ID_RE_TEMPLATE = r"\s(?:id|name)=[\'\"]{}[\'\"]"


def _split_href(href: str | None) -> tuple[str | None, str | None]:
    if not href:
        return None, None
    base, _, fragment = href.partition("#")
    return urllib.parse.unquote(base) or None, urllib.parse.unquote(fragment) or None


def _fragment_offset(doc: SourceDocument | None, fragment: str | None) -> tuple[int | None, int | None, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    if doc is None or not fragment:
        return None, None, diagnostics
    pattern = re.compile(_ID_RE_TEMPLATE.format(re.escape(fragment)))
    match = pattern.search(doc.text)
    if not match:
        diagnostics.append(Diagnostic("warning", "unresolved_fragment", f"Fragment {fragment!r} was not found", doc.href))
        return None, None, diagnostics
    return match.start(), byte_offset(doc.char_to_byte, match.start()), diagnostics


def navigation_from_parser(parser: Any, documents: list[SourceDocument] | None = None) -> list[NavigationEntry]:
    try:
        parser._process_epub_content_nav()
    except ValueError:
        return [NavigationEntry("nav:0:fallback", "Document", None, None, None, None, None, None, 1, None, 0, (), "fallback", [Diagnostic("warning", "missing_nav", "No navigation document found")])]

    docs_by_href = {doc.href: doc for doc in documents or []}
    docs_by_href.update({urllib.parse.unquote(doc.href): doc for doc in documents or []})
    entries: list[NavigationEntry] = []
    child_map: dict[str, list[str]] = {}

    def walk(nodes: list[dict[str, Any]], level: int, parent_id: str | None) -> None:
        for node in nodes:
            order = len(entries)
            title = node.get("title") or "Untitled"
            href = node.get("src")
            doc_href, fragment = _split_href(href)
            doc = docs_by_href.get(doc_href or "")
            source_start, byte_start, diagnostics = _fragment_offset(doc, fragment)
            if doc_href and doc is None and documents is not None:
                diagnostics.append(Diagnostic("warning", "unresolved_href", f"Navigation href {doc_href!r} was not found"))
            nav_id = f"nav:{order}:{stable_hash((href or '') + title)}"
            entries.append(NavigationEntry(nav_id, title, href, doc.href if doc else doc_href, fragment, doc.spine_index if doc else None, source_start, byte_start, level, parent_id, order, (), "nav", diagnostics))
            if parent_id:
                child_map.setdefault(parent_id, []).append(nav_id)
            walk(node.get("children", []), level + 1, nav_id)

    walk(parser.processed_nav_structure, 1, None)
    if child_map:
        entries = [entry if entry.id not in child_map else NavigationEntry(**{**entry.__dict__, "children": tuple(child_map[entry.id])}) for entry in entries]
    return entries
