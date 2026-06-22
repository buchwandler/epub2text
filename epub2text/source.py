"""Source document decoding and offset helpers."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from .diagnostics import Diagnostic
from .structured import SourceDocument, stable_hash

_ENCODING_RE = re.compile(rb"<\?xml[^>]*encoding=['\"]([^'\"]+)", re.I)
_META_CHARSET_RE = re.compile(rb"<meta[^>]+charset=['\"]?([^\s'\"/>]+)", re.I)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_encoding(raw: bytes) -> tuple[str, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    for pattern in (_ENCODING_RE, _META_CHARSET_RE):
        match = pattern.search(raw[:2048])
        if match:
            try:
                return match.group(1).decode("ascii"), diagnostics
            except UnicodeDecodeError:
                break
    return "utf-8", diagnostics


def decode_source(raw: bytes) -> tuple[str, str, list[Diagnostic]]:
    encoding, diagnostics = detect_encoding(raw)
    try:
        return raw.decode(encoding), encoding, diagnostics
    except (LookupError, UnicodeDecodeError):
        diagnostics.append(
            Diagnostic(
                "warning",
                "encoding_fallback",
                f"Could not decode as {encoding}; used utf-8 replacement",
            )
        )
        return raw.decode("utf-8", errors="replace"), "utf-8", diagnostics


def build_char_to_byte(text: str, encoding: str) -> list[int] | None:
    offsets = [0]
    total = 0
    try:
        for char in text:
            total += len(char.encode(encoding))
            offsets.append(total)
    except UnicodeEncodeError:
        return None
    return offsets


def byte_offset(table: list[int] | None, char_offset: int | None) -> int | None:
    if (
        table is None
        or char_offset is None
        or char_offset < 0
        or char_offset >= len(table)
    ):
        return None
    return table[char_offset]


def source_document_from_item(
    item: Any,
    *,
    spine_index: int | None,
    document_id: str | None = None,
    include_byte_offsets: bool = True,
) -> SourceDocument:
    raw = item.get_content()
    text, encoding, diagnostics = decode_source(raw)
    char_to_byte = build_char_to_byte(text, encoding) if include_byte_offsets else None
    href = item.get_name()
    return SourceDocument(
        document_id=document_id
        or getattr(item, "id", None)
        or f"doc:{spine_index}:{stable_hash(href)}",
        href=href,
        spine_index=spine_index,
        media_type=getattr(item, "media_type", None),
        raw_bytes_sha256=sha256_bytes(raw),
        raw_bytes_len=len(raw),
        encoding=encoding,
        text=text,
        text_sha256=hashlib.sha256(
            text.encode("utf-8", errors="surrogatepass")
        ).hexdigest(),
        char_to_byte=char_to_byte,
        diagnostics=diagnostics,
    )
