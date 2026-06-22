"""Read-only EPUB package and spine inspection."""

from __future__ import annotations

from typing import Any

import ebooklib  # type: ignore[import-untyped]
from ebooklib import epub

from .diagnostics import Diagnostic
from .source import sha256_bytes, source_document_from_item
from .structured import EpubManifestItem, EpubPackageInfo, EpubSpineItem, SourceDocument


def _item_properties(item: Any) -> tuple[str, ...]:
    props = getattr(item, "properties", ()) or ()
    if isinstance(props, str):
        return tuple(props.split())
    return tuple(str(p) for p in props)


def inspect_package(parser: Any) -> EpubPackageInfo:
    diagnostics: list[Diagnostic] = []
    manifest_items: list[EpubManifestItem] = []
    nav_href = None
    ncx_href = None
    for item in parser.book.get_items():
        raw = None
        raw_size = None
        digest = None
        try:
            raw = item.get_content()
            raw_size = len(raw)
            digest = sha256_bytes(raw)
        except Exception:
            pass
        href = item.get_name()
        media_type = getattr(item, "media_type", None)
        props = _item_properties(item)
        if (
            getattr(item, "type", None) == ebooklib.ITEM_NAVIGATION
            or "nav" in props
            or href.lower().endswith(("nav.xhtml", "nav.html"))
            or (raw and b"epub:type=\"toc\"" in raw[:4096])
        ):
            nav_href = href
        if href.lower().endswith(".ncx") or media_type == "application/x-dtbncx+xml":
            ncx_href = href
        manifest_items.append(EpubManifestItem(getattr(item, "id", href), href, media_type, props, raw_size, digest))

    spine: list[EpubSpineItem] = []
    for index, spine_tuple in enumerate(parser.book.spine):
        item_id = spine_tuple[0]
        linear = len(spine_tuple) < 2 or str(spine_tuple[1]).lower() != "no"
        item = parser.book.get_item_with_id(item_id)
        if item is None:
            diagnostics.append(Diagnostic("warning", "unresolved_href", f"Spine item {item_id} was not found"))
            continue
        spine.append(EpubSpineItem(item_id, item.get_name(), index, linear, getattr(item, "media_type", None)))

    return EpubPackageInfo(
        source_path=str(parser.filepath),
        package_sha256=sha256_bytes(parser.filepath.read_bytes()),
        opf_href=getattr(getattr(parser.book, "container", None), "opf_name", None),
        epub_version=getattr(parser.book, "version", None),
        metadata=parser.get_metadata(),
        manifest_items=manifest_items,
        spine=spine,
        nav_href=nav_href,
        ncx_href=ncx_href,
        diagnostics=diagnostics,
    )


def get_spine_documents(
    parser: Any,
    *,
    include_byte_offsets: bool = True,
    include_non_linear: bool = False,
    include_nav_documents: bool = False,
) -> list[SourceDocument]:
    docs: list[SourceDocument] = []
    for index, spine_tuple in enumerate(parser.book.spine):
        item_id = spine_tuple[0]
        linear = len(spine_tuple) < 2 or str(spine_tuple[1]).lower() != "no"
        if not linear and not include_non_linear:
            continue
        item = parser.book.get_item_with_id(item_id)
        if item is None:
            continue
        props = _item_properties(item)
        if not include_nav_documents and (getattr(item, "type", None) == ebooklib.ITEM_NAVIGATION or "nav" in props or item.get_name() == inspect_package(parser).nav_href):
            continue
        doc_id = f"doc:{index}:{item_id}"
        docs.append(source_document_from_item(item, spine_index=index, document_id=doc_id, include_byte_offsets=include_byte_offsets))
    return docs
