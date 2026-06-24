"""Public structured extraction models and JSON export helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields, is_dataclass
from hashlib import sha1
from typing import Any, Literal

from .diagnostics import Diagnostic
from .models import Metadata

DEFAULT_TEXT_BLOCK_TAGS = frozenset(
    {
        "p",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "li",
        "td",
        "th",
        "caption",
        "dt",
        "dd",
        "figcaption",
        "blockquote",
    }
)
DEFAULT_SKIP_TAGS = frozenset({"head", "title", "script", "style", "noscript"})
DEFAULT_ALLOWED_INLINE_FRAGMENT_TAGS = frozenset(
    {
        "a",
        "abbr",
        "b",
        "bdi",
        "bdo",
        "br",
        "cite",
        "code",
        "data",
        "dfn",
        "em",
        "i",
        "kbd",
        "mark",
        "q",
        "rp",
        "rt",
        "ruby",
        "s",
        "samp",
        "small",
        "span",
        "strong",
        "sub",
        "sup",
        "time",
        "u",
        "var",
        "wbr",
    }
)
DEFAULT_ALLOWED_INLINE_FRAGMENT_ATTRS = (
    ("*", frozenset({"class", "id", "lang", "xml:lang", "dir", "title", "epub:type"})),
    ("a", frozenset({"href"})),
    (
        "span",
        frozenset({"class", "id", "lang", "xml:lang", "dir", "title", "epub:type"}),
    ),
)
SCHEMA_VERSION = "epub2text.structured.v1"


@dataclass(frozen=True)
class ExtractionPolicy:
    block_tags: frozenset[str] = DEFAULT_TEXT_BLOCK_TAGS
    skip_tags: frozenset[str] = DEFAULT_SKIP_TAGS
    opaque_inline_tags: frozenset[str] = frozenset({"code", "kbd", "samp", "var", "tt"})
    include_footnotes: bool = True
    include_sup_sub: bool = True
    normalize_whitespace: bool = False
    remove_duplicate_titles: bool = False
    include_nav_documents: bool = False
    include_non_linear_spine: bool = False
    strict_offsets: bool = False
    allowed_inline_fragment_tags: frozenset[str] = DEFAULT_ALLOWED_INLINE_FRAGMENT_TAGS
    allowed_inline_fragment_attrs: tuple[tuple[str, frozenset[str]], ...] = (
        DEFAULT_ALLOWED_INLINE_FRAGMENT_ATTRS
    )


@dataclass(frozen=True)
class EpubManifestItem:
    id: str
    href: str
    media_type: str | None
    properties: tuple[str, ...]
    raw_size: int | None
    sha256: str | None


@dataclass(frozen=True)
class EpubSpineItem:
    item_id: str
    href: str
    index: int
    linear: bool
    media_type: str | None


@dataclass(frozen=True)
class EpubPackageInfo:
    source_path: str
    package_sha256: str
    opf_href: str | None
    epub_version: str | None
    metadata: Metadata
    manifest_items: list[EpubManifestItem]
    spine: list[EpubSpineItem]
    nav_href: str | None
    ncx_href: str | None
    diagnostics: list[Diagnostic]


@dataclass(frozen=True)
class SourceDocument:
    document_id: str
    href: str
    spine_index: int | None
    media_type: str | None
    raw_bytes_sha256: str
    raw_bytes_len: int
    encoding: str
    text: str
    text_sha256: str
    char_to_byte: list[int] | None
    diagnostics: list[Diagnostic]


@dataclass(frozen=True)
class NavigationEntry:
    id: str
    title: str
    href: str | None
    document_href: str | None
    fragment: str | None
    spine_index: int | None
    source_char_start: int | None
    source_byte_start: int | None
    level: int
    parent_id: str | None
    order: int
    children: tuple[str, ...]
    source: str
    diagnostics: list[Diagnostic]


@dataclass(frozen=True)
class SourceRange:
    document_id: str
    source_char_start: int
    source_char_end: int
    source_byte_start: int | None = None
    source_byte_end: int | None = None


@dataclass(frozen=True)
class TextRun:
    kind: Literal["text"]
    text: str
    source_char_start: int
    source_char_end: int
    source_byte_start: int | None
    source_byte_end: int | None
    block_text_start: int
    block_text_end: int


InlineTagKind = Literal["inline_start", "inline_end", "inline_empty", "opaque_inline"]


@dataclass(frozen=True)
class InlineTagRun:
    kind: InlineTagKind
    tag_name: str
    raw: str
    source_char_start: int
    source_char_end: int
    source_byte_start: int | None
    source_byte_end: int | None
    attrs: tuple[tuple[str, str], ...]
    block_text_start: int | None = None
    block_text_end: int | None = None


@dataclass(frozen=True)
class EntityRun:
    kind: Literal["entity"]
    raw: str
    text: str
    source_char_start: int
    source_char_end: int
    block_text_start: int
    block_text_end: int


ContentRun = TextRun | InlineTagRun | EntityRun


@dataclass(frozen=True)
class XhtmlFragment:
    text: str
    xhtml: str
    tag_skeleton: tuple[str, ...]
    source_char_start: int | None
    source_char_end: int | None
    diagnostics: list[Diagnostic]


@dataclass(frozen=True)
class TextBlock:
    id: str
    document_id: str
    document_href: str
    spine_index: int | None
    block_index: int
    tag_name: str
    element_path: str
    attrs: tuple[tuple[str, str], ...]
    outer_char_start: int
    outer_char_end: int
    inner_char_start: int
    inner_char_end: int
    outer_byte_start: int | None
    outer_byte_end: int | None
    inner_byte_start: int | None
    inner_byte_end: int | None
    text: str
    text_sha256: str
    runs: list[ContentRun]
    chapter_id: str | None
    chapter_title: str | None
    page_number: str | None
    extraction_policy: str
    diagnostics: list[Diagnostic]
    xhtml_fragment: XhtmlFragment | None = None


@dataclass(frozen=True)
class TextSegment:
    id: str
    block_id: str
    mode: str
    index: int
    text: str
    block_text_start: int
    block_text_end: int
    document_text_ranges: tuple[SourceRange, ...]
    chapter_id: str | None
    page_number: str | None
    diagnostics: list[Diagnostic]
    xhtml_fragment: XhtmlFragment | None = None


def stable_hash(value: str, length: int = 8) -> str:
    return sha1(value.encode("utf-8", errors="surrogatepass")).hexdigest()[:length]


def _convert(
    obj: Any,
    *,
    include_raw: bool,
    include_runs: bool,
    include_segments: bool,
    include_xhtml_fragments: bool,
) -> Any:
    if is_dataclass(obj):
        result = {}
        for field in fields(obj):
            if (
                field.name == "text"
                and obj.__class__.__name__ == "SourceDocument"
                and not include_raw
            ):
                continue
            if (
                field.name == "char_to_byte"
                and obj.__class__.__name__ == "SourceDocument"
                and not include_raw
            ):
                continue
            if field.name == "runs" and not include_runs:
                continue
            if field.name == "xhtml_fragment" and (
                not include_xhtml_fragments or getattr(obj, field.name) is None
            ):
                continue
            result[field.name] = _convert(
                getattr(obj, field.name),
                include_raw=include_raw,
                include_runs=include_runs,
                include_segments=include_segments,
                include_xhtml_fragments=include_xhtml_fragments,
            )
        return result
    if isinstance(obj, list):
        return [
            _convert(
                item,
                include_raw=include_raw,
                include_runs=include_runs,
                include_segments=include_segments,
                include_xhtml_fragments=include_xhtml_fragments,
            )
            for item in obj
        ]
    if isinstance(obj, tuple | frozenset):
        return [
            _convert(
                item,
                include_raw=include_raw,
                include_runs=include_runs,
                include_segments=include_segments,
                include_xhtml_fragments=include_xhtml_fragments,
            )
            for item in obj
        ]
    return obj


@dataclass(frozen=True)
class StructuredEpubExtraction:
    source_path: str
    source_sha256: str
    package: EpubPackageInfo
    documents: list[SourceDocument]
    navigation: list[NavigationEntry]
    blocks: list[TextBlock]
    segments: list[TextSegment]
    diagnostics: list[Diagnostic]

    def to_dict(
        self,
        *,
        include_raw: bool = False,
        include_runs: bool = True,
        include_segments: bool = True,
        include_xhtml_fragments: bool = False,
    ) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "source": {"path": self.source_path, "sha256": self.source_sha256},
            "package": _convert(
                self.package,
                include_raw=include_raw,
                include_runs=include_runs,
                include_segments=include_segments,
                include_xhtml_fragments=include_xhtml_fragments,
            ),
            "documents": _convert(
                self.documents,
                include_raw=include_raw,
                include_runs=include_runs,
                include_segments=include_segments,
                include_xhtml_fragments=include_xhtml_fragments,
            ),
            "navigation": _convert(
                self.navigation,
                include_raw=include_raw,
                include_runs=include_runs,
                include_segments=include_segments,
                include_xhtml_fragments=include_xhtml_fragments,
            ),
            "blocks": _convert(
                self.blocks,
                include_raw=include_raw,
                include_runs=include_runs,
                include_segments=include_segments,
                include_xhtml_fragments=include_xhtml_fragments,
            ),
            "segments": _convert(
                self.segments if include_segments else [],
                include_raw=include_raw,
                include_runs=include_runs,
                include_segments=include_segments,
                include_xhtml_fragments=include_xhtml_fragments,
            ),
            "diagnostics": _convert(
                self.diagnostics,
                include_raw=include_raw,
                include_runs=include_runs,
                include_segments=include_segments,
                include_xhtml_fragments=include_xhtml_fragments,
            ),
        }

    def to_json(
        self,
        *,
        include_raw: bool = False,
        include_runs: bool = True,
        include_segments: bool = True,
        include_xhtml_fragments: bool = False,
        indent: int | None = None,
    ) -> str:
        return json.dumps(
            self.to_dict(
                include_raw=include_raw,
                include_runs=include_runs,
                include_segments=include_segments,
                include_xhtml_fragments=include_xhtml_fragments,
            ),
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
        )


def extract_epub_structure(
    filepath: str,
    *,
    include_raw_documents: bool = False,
    include_offsets: bool = True,
    include_inline_runs: bool = True,
    include_segments: bool = False,
    include_xhtml_fragments: bool = False,
    policy: ExtractionPolicy | None = None,
) -> StructuredEpubExtraction:
    from .parser import EPUBParser

    parser = EPUBParser(filepath)
    return parser.extract_structured(
        policy=policy,
        include_raw_documents=include_raw_documents,
        include_offsets=include_offsets,
        include_inline_runs=include_inline_runs,
        include_segments=include_segments,
        include_xhtml_fragments=include_xhtml_fragments,
    )
