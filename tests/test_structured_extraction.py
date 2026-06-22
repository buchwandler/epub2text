import json

from ebooklib import epub

from epub2text import EPUBParser, extract_epub_structure


def make_epub(path):
    book = epub.EpubBook()
    book.set_identifier("id")
    book.set_title("Structured Test")
    book.set_language("en")
    chapter = epub.EpubHtml(title="Chapter", file_name="chap.xhtml", lang="en")
    chapter.content = """<html><body><h1 id="c1">Chapter</h1><p>Hello <em>world</em> &amp; A&nbsp;B<sup>1</sup></p><ol start="4"><li>Alpha</li><li>Beta</li></ol></body></html>"""  # noqa: E501
    book.add_item(chapter)
    book.add_item(epub.EpubNav())
    book.add_item(epub.EpubNcx())
    book.toc = (epub.Link("chap.xhtml#c1", "Chapter", "c1"),)
    book.spine = ["nav", chapter]
    epub.write_epub(str(path), book)


def test_structured_extraction_blocks_runs_entities_and_json(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub(epub_path)

    parser = EPUBParser(str(epub_path))
    extraction = parser.extract_structured(include_segments=True)

    assert parser.inspect_package().nav_href == "nav.xhtml"
    assert [doc.href for doc in extraction.documents] == ["chap.xhtml"]
    texts = [block.text for block in extraction.blocks]
    assert "Hello world & A\xa0B1" in texts
    assert "Alpha" in texts
    assert "Beta" in texts
    assert all("__TAG_" not in text and "__SPANTX_" not in text for text in texts)

    paragraph = next(block for block in extraction.blocks if block.tag_name == "p")
    assert (
        "<p"
        in extraction.documents[0].text[
            paragraph.outer_char_start : paragraph.outer_char_end
        ]
    )
    assert "<em>" in [getattr(run, "raw", None) for run in paragraph.runs]
    assert any(
        getattr(run, "raw", None) == "&amp;" and run.text == "&"
        for run in paragraph.runs
    )
    assert "\xa0" in paragraph.text
    assert "".join(getattr(run, "text", "") for run in paragraph.runs) == paragraph.text

    for segment in extraction.segments:
        block = next(
            block for block in extraction.blocks if block.id == segment.block_id
        )
        assert (
            block.text[segment.block_text_start : segment.block_text_end]
            == segment.text
        )

    payload = extraction.to_json(include_raw=False, indent=2)
    assert payload == parser.extract_structured(include_segments=True).to_json(
        include_raw=False, indent=2
    )
    decoded = json.loads(payload)
    assert decoded["schema"] == "epub2text.structured.v1"
    assert "text" not in decoded["documents"][0]


def test_extract_epub_structure_convenience(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub(epub_path)
    extraction = extract_epub_structure(str(epub_path), include_segments=True)
    assert extraction.blocks
    assert extraction.segments
