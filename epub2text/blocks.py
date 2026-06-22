"""Offset-preserving text block extraction."""

from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from hashlib import sha256
from html.parser import HTMLParser
from typing import Any

from .source import byte_offset
from .structured import EntityRun, ExtractionPolicy, InlineTagRun, SourceDocument, TextBlock, TextRun, stable_hash

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


@dataclass
class _OpenBlock:
    tag: str
    attrs: tuple[tuple[str, str], ...]
    path: str
    outer_start: int
    inner_start: int
    text_parts: list[str] = field(default_factory=list)
    runs: list[Any] = field(default_factory=list)

    @property
    def text_len(self) -> int:
        return sum(len(part) for part in self.text_parts)

    def add_text(self, text: str, start: int, end: int, table: list[int] | None) -> None:
        if not text:
            return
        text_start = self.text_len
        self.text_parts.append(text)
        self.runs.append(TextRun("text", text, start, end, byte_offset(table, start), byte_offset(table, end), text_start, text_start + len(text)))

    def add_entity(self, raw: str, text: str, start: int, end: int) -> None:
        text_start = self.text_len
        self.text_parts.append(text)
        self.runs.append(EntityRun("entity", raw, text, start, end, text_start, text_start + len(text)))


class OffsetBlockParser(HTMLParser):
    def __init__(self, document: SourceDocument, policy: ExtractionPolicy):
        super().__init__(convert_charrefs=False)
        self.document = document
        self.policy = policy
        self.line_starts = self._line_starts(document.text)
        self.stack: list[tuple[str, int]] = []
        self.open_blocks: list[_OpenBlock] = []
        self.blocks: list[TextBlock] = []
        self.block_counter = 0

    @staticmethod
    def _line_starts(text: str) -> list[int]:
        starts = [0]
        for match in re.finditer("\n", text):
            starts.append(match.end())
        return starts

    def _offset(self) -> int:
        line, col = self.getpos()
        return self.line_starts[line - 1] + col

    def _attrs(self, attrs: list[tuple[str, str | None]]) -> tuple[tuple[str, str], ...]:
        return tuple((name, value or "") for name, value in attrs)

    def _path(self, tag: str) -> str:
        counts: dict[str, int] = {}
        parts = []
        for name, _ in self.stack + [(tag, 0)]:
            counts[name] = counts.get(name, 0) + 1
            parts.append(f"{name}[{counts[name]}]")
        return "/" + "/".join(parts)

    def _skipped(self) -> bool:
        return any(tag in self.policy.skip_tags for tag, _ in self.stack)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        start = self._offset()
        raw = self.get_starttag_text() or self.document.text[start:start]
        end = start + len(raw)
        attrs_tuple = self._attrs(attrs)
        if self.open_blocks and tag not in self.policy.block_tags:
            kind = "inline_empty" if tag in VOID_TAGS else "opaque_inline" if tag in self.policy.opaque_inline_tags else "inline_start"
            self.open_blocks[-1].runs.append(InlineTagRun(kind, tag, raw, start, end, byte_offset(self.document.char_to_byte, start), byte_offset(self.document.char_to_byte, end), attrs_tuple))
        if not self._skipped() and tag in self.policy.block_tags:
            self.open_blocks.append(_OpenBlock(tag, attrs_tuple, self._path(tag), start, end))
        if tag not in VOID_TAGS:
            self.stack.append((tag, start))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        start = self._offset()
        raw = self.get_starttag_text() or self.document.text[start:start]
        end = start + len(raw)
        attrs_tuple = self._attrs(attrs)
        if self.open_blocks and tag not in self.policy.block_tags:
            kind = "opaque_inline" if tag in self.policy.opaque_inline_tags else "inline_empty"
            self.open_blocks[-1].runs.append(InlineTagRun(kind, tag, raw, start, end, byte_offset(self.document.char_to_byte, start), byte_offset(self.document.char_to_byte, end), attrs_tuple))

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        end_start = self._offset()
        raw_match = re.match(r"</\s*[^>]+>", self.document.text[end_start:])
        raw = raw_match.group(0) if raw_match else f"</{tag}>"
        end = end_start + len(raw)
        if self.open_blocks and tag not in self.policy.block_tags:
            self.open_blocks[-1].runs.append(InlineTagRun("inline_end", tag, raw, end_start, end, byte_offset(self.document.char_to_byte, end_start), byte_offset(self.document.char_to_byte, end), ()))
        if self.open_blocks and self.open_blocks[-1].tag == tag:
            block = self.open_blocks.pop()
            text = "".join(block.text_parts)
            block_id = f"block:{self.document.document_id}:{self.block_counter}:{block.inner_start}:{stable_hash(text)}"
            self.blocks.append(TextBlock(
                block_id, self.document.document_id, self.document.href, self.document.spine_index, self.block_counter,
                block.tag, block.path, block.attrs, block.outer_start, end, block.inner_start, end_start,
                byte_offset(self.document.char_to_byte, block.outer_start), byte_offset(self.document.char_to_byte, end),
                byte_offset(self.document.char_to_byte, block.inner_start), byte_offset(self.document.char_to_byte, end_start),
                text, sha256(text.encode("utf-8", errors="surrogatepass")).hexdigest(), block.runs,
                None, None, None, "structured-default", []))
            self.block_counter += 1
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data: str) -> None:
        if self.open_blocks and not self._skipped():
            start = self._offset()
            self.open_blocks[-1].add_text(data, start, start + len(data), self.document.char_to_byte)

    def handle_entityref(self, name: str) -> None:
        if self.open_blocks and not self._skipped():
            start = self._offset()
            raw = f"&{name};"
            self.open_blocks[-1].add_entity(raw, html.unescape(raw), start, start + len(raw))

    def handle_charref(self, name: str) -> None:
        if self.open_blocks and not self._skipped():
            start = self._offset()
            raw = f"&#{name};"
            self.open_blocks[-1].add_entity(raw, html.unescape(raw), start, start + len(raw))


def extract_blocks(document: SourceDocument, policy: ExtractionPolicy | None = None) -> list[TextBlock]:
    parser = OffsetBlockParser(document, policy or ExtractionPolicy())
    parser.feed(document.text)
    parser.close()
    return parser.blocks
