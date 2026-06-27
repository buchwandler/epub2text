"""Tests for URL-based EPUB downloads."""

from __future__ import annotations

import contextlib
import threading
import time
from collections.abc import Generator
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pypub
import pytest

from epub2text import epub2txt


class QuietHandler(SimpleHTTPRequestHandler):
    """HTTP handler that suppresses logs."""

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        return


class SlowHandler(QuietHandler):
    """HTTP handler that delays responses."""

    def do_GET(self) -> None:  # noqa: N802
        time.sleep(0.2)
        super().do_GET()


@contextmanager
def serve_directory(
    directory: Path, handler_cls: type[SimpleHTTPRequestHandler] = QuietHandler
) -> Generator[str]:
    handler = partial(handler_cls, directory=str(directory))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address[:2]
        host_value = host.decode() if isinstance(host, bytes) else host
        yield f"http://{host_value}:{port}"
    finally:
        # Stop the loop, then close the listening socket to avoid FD/memory growth
        with contextlib.suppress(Exception):
            server.shutdown()
        thread.join(timeout=5)
        with contextlib.suppress(Exception):
            server.server_close()


def _create_epub(epub_path: Path) -> None:
    book = pypub.Epub("Download Test", creator="Downloader")
    chapter = pypub.create_chapter_from_text(
        "This is a downloadable EPUB.",
        title="Chapter 1",
    )
    book.add_chapter(chapter)
    book.create(str(epub_path))


def test_epub2txt_downloads_from_url(tmp_path: Path) -> None:
    epub_path = tmp_path / "download.epub"
    _create_epub(epub_path)

    with serve_directory(tmp_path) as base_url:
        text = epub2txt(f"{base_url}/{epub_path.name}")
        assert isinstance(text, str)

    assert "downloadable epub" in text.lower()


def test_epub2txt_rejects_oversize_download(tmp_path: Path) -> None:
    epub_path = tmp_path / "oversize.epub"
    _create_epub(epub_path)

    with serve_directory(tmp_path) as base_url:
        with pytest.raises(ValueError):
            epub2txt(f"{base_url}/{epub_path.name}", max_bytes=100)


def test_epub2txt_download_timeout(tmp_path: Path) -> None:
    epub_path = tmp_path / "slow.epub"
    _create_epub(epub_path)

    with serve_directory(tmp_path, handler_cls=SlowHandler) as base_url:
        with pytest.raises(TimeoutError):
            epub2txt(f"{base_url}/{epub_path.name}", timeout=(0.05, 0.05))
