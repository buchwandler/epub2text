"""
epub2text - Extract text from EPUB files with smart cleaning.

A niche CLI tool for extracting and processing text from EPUB files.
Supports selective chapter extraction, smart text cleaning, and
both CLI and library usage.
"""

import os
import socket
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Union
from .parser import EPUBParser
from .models import Chapter, Metadata, Page, PageSource
from .cleaner import clean_text, TextCleaner
from .bookmarks import Bookmark, BookmarkManager
from .reader import EpubReader, ReaderState
from .diagnostics import Diagnostic, StrictExtractionError
from .structured import (
    EntityRun,
    EpubManifestItem,
    EpubPackageInfo,
    EpubSpineItem,
    ExtractionPolicy,
    InlineTagRun,
    NavigationEntry,
    SourceDocument,
    StructuredEpubExtraction,
    TextBlock,
    TextRun,
    TextSegment,
    extract_epub_structure,
)

__all__ = [
    "EPUBParser",
    "Chapter",
    "Metadata",
    "Page",
    "PageSource",
    "clean_text",
    "TextCleaner",
    "epub2txt",
    "Bookmark",
    "BookmarkManager",
    "EpubReader",
    "ReaderState",
    "Diagnostic",
    "StrictExtractionError",
    "ExtractionPolicy",
    "EpubPackageInfo",
    "EpubManifestItem",
    "EpubSpineItem",
    "SourceDocument",
    "NavigationEntry",
    "TextBlock",
    "TextSegment",
    "TextRun",
    "InlineTagRun",
    "EntityRun",
    "StructuredEpubExtraction",
    "extract_epub_structure",
]

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0+unknown"


DEFAULT_DOWNLOAD_TIMEOUT: tuple[float, float] = (10.0, 30.0)
DEFAULT_MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024


def _looks_like_epub(data: bytes) -> bool:
    return data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))


def _apply_read_timeout(response: Any, timeout: float) -> None:
    try:
        raw = response.fp
        if hasattr(raw, "raw") and hasattr(raw.raw, "_sock"):
            raw.raw._sock.settimeout(timeout)
        elif hasattr(raw, "_sock"):
            raw._sock.settimeout(timeout)
    except Exception:
        return


def _download_epub(
    url: str,
    *,
    timeout: float | tuple[float, float],
    max_bytes: int,
    user_agent: str,
    allowed_schemes: tuple[str, ...],
) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in allowed_schemes:
        raise ValueError(
            f"URL scheme '{parsed.scheme}' is not allowed. "
            f"Allowed schemes: {', '.join(allowed_schemes)}"
        )

    connect_timeout: float
    read_timeout: float
    if isinstance(timeout, tuple):
        connect_timeout, read_timeout = timeout
    else:
        connect_timeout = timeout
        read_timeout = timeout

    request = urllib.request.Request(url, headers={"User-Agent": user_agent})
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as tmp:
            tmp_path = tmp.name

        with urllib.request.urlopen(request, timeout=connect_timeout) as response:
            _apply_read_timeout(response, read_timeout)
            content_length = response.headers.get("Content-Length")
            content_size: int | None = None
            if content_length:
                try:
                    content_size = int(content_length)
                except ValueError:
                    content_size = None
            if content_size is not None and content_size > max_bytes:
                raise ValueError(f"Download exceeds size limit of {max_bytes:,} bytes")

            bytes_read = 0
            chunk_size = 1024 * 1024
            with open(tmp_path, "wb") as output_file:
                first_chunk = response.read(chunk_size)
                if not first_chunk:
                    raise ValueError("Empty response while downloading EPUB")
                if not _looks_like_epub(first_chunk):
                    raise ValueError("URL did not return a valid EPUB (ZIP) file")

                output_file.write(first_chunk)
                bytes_read += len(first_chunk)

                if bytes_read > max_bytes:
                    raise ValueError(
                        f"Download exceeds size limit of {max_bytes:,} bytes"
                    )

                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    bytes_read += len(chunk)
                    if bytes_read > max_bytes:
                        raise ValueError(
                            f"Download exceeds size limit of {max_bytes:,} bytes"
                        )
                    output_file.write(chunk)

                output_file.flush()
                os.fsync(output_file.fileno())

        return tmp_path
    except Exception as exc:
        if tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
        if isinstance(exc, urllib.error.URLError | socket.timeout):
            if isinstance(exc, socket.timeout) or isinstance(
                getattr(exc, "reason", None), socket.timeout
            ):
                raise TimeoutError(f"Timed out while downloading {url}") from exc
        raise


def epub2txt(
    filepath: str,
    outputlist: bool = False,
    clean: bool = True,
    timeout: float | tuple[float, float] = DEFAULT_DOWNLOAD_TIMEOUT,
    max_bytes: int = DEFAULT_MAX_DOWNLOAD_BYTES,
    user_agent: str | None = None,
    allowed_schemes: tuple[str, ...] = ("https", "http"),
) -> str | list[str]:
    """
    Extract text from EPUB file (compatibility function for old epub2txt API).

    Args:
        filepath: Path to EPUB file or URL
        outputlist: If True, return list of chapter texts; if False,
            return single string
        clean: If True, apply text cleaning; if False, minimal processing
        timeout: Connection/read timeout for URL downloads (seconds)
        max_bytes: Maximum allowed download size for URLs
        user_agent: Optional User-Agent header for URL downloads
        allowed_schemes: Allowed URL schemes for downloads

    Returns:
        Either a single string of all text (outputlist=False) or list of
        chapter texts (outputlist=True)

    Examples:
        >>> text = epub2txt("book.epub")
        >>> chapters = epub2txt("book.epub", outputlist=True)
        >>> raw_text = epub2txt("book.epub", clean=False)
        >>> text = epub2txt("https://example.com/book.epub")
    """
    # Check if filepath is a URL
    is_url = filepath.startswith("http://") or filepath.startswith("https://")

    tmp_path: str | None = None
    if is_url:
        # Download to temporary file
        try:
            user_agent = user_agent or f"epub2text/{__version__}"
            tmp_path = _download_epub(
                filepath,
                timeout=timeout,
                max_bytes=max_bytes,
                user_agent=user_agent,
                allowed_schemes=allowed_schemes,
            )
            actual_path = tmp_path
        except Exception:
            # Clean up temporary file on download failure
            if tmp_path and Path(tmp_path).exists():
                Path(tmp_path).unlink(missing_ok=True)
            raise
    else:
        actual_path = filepath

    try:
        # Use compact format (single newlines) to match old epub2txt behavior
        parser = EPUBParser(actual_path, paragraph_separator="\n")

        # Get all chapters
        chapters = parser.get_chapters()

        if outputlist:
            # Return list of chapter texts
            result = []
            for chapter in chapters:
                text = parser.extract_chapters([chapter.id])
                if clean:
                    cleaner = TextCleaner(preserve_single_newlines=True)
                    text = cleaner.clean(text)
                result.append(text)
            return result
        else:
            # Return single concatenated string
            text = parser.extract_chapters()
            if clean:
                cleaner = TextCleaner(preserve_single_newlines=True)
                text = cleaner.clean(text)
            return text
    finally:
        # Clean up temporary file if we downloaded one
        if is_url and tmp_path:
            Path(tmp_path).unlink(missing_ok=True)
