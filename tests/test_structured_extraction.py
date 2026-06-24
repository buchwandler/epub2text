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


def make_epub_with_body(path, body):
    book = epub.EpubBook()
    book.set_identifier("id")
    book.set_title("Structured Test")
    book.set_language("en")
    chapter = epub.EpubHtml(title="Chapter", file_name="chap.xhtml", lang="en")
    chapter.content = f"<html><body>{body}</body></html>"
    book.add_item(chapter)
    book.add_item(epub.EpubNav())
    book.add_item(epub.EpubNcx())
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


def visible_text(xhtml):
    from html.parser import HTMLParser

    class Parser(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.parts = []

        def handle_data(self, data):
            self.parts.append(data)

    parser = Parser()
    parser.feed(xhtml)
    return "".join(parser.parts)


def test_xhtml_block_fragment_preserves_inline_emphasis(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(epub_path, "<p>A <em>small</em> test.</p>")
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_xhtml_fragments=True
    )
    block = next(block for block in extraction.blocks if block.tag_name == "p")
    assert block.text == "A small test."
    assert block.xhtml_fragment.xhtml == "A <em>small</em> test."
    assert block.xhtml_fragment.text == block.text


def test_xhtml_segment_fragment_includes_wrapping_emphasis(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(
        epub_path,
        "<p>Plain. <em>Running down again – always at the worst "
        "possible moment!</em></p>",
    )
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_segments=True, include_xhtml_fragments=True
    )
    segment = next(
        segment
        for segment in extraction.segments
        if segment.text.strip().startswith("Running")
    )
    assert segment.text == "Running down again – always at the worst possible moment!"
    assert (
        segment.xhtml_fragment.xhtml
        == "<em>Running down again – always at the worst possible moment!</em>"
    )


def test_xhtml_nested_inline_tags_remain_balanced(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(
        epub_path, '<p>A <span class="ship"><em>Esca Volenti</em></span> shuddered.</p>'
    )
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_xhtml_fragments=True
    )
    block = next(block for block in extraction.blocks if block.tag_name == "p")
    assert (
        block.xhtml_fragment.xhtml
        == 'A <span class="ship"><em>Esca Volenti</em></span> shuddered.'
    )


def test_xhtml_entities_preserve_visible_text_equivalence(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(epub_path, "<p>A&nbsp;B &amp; C</p>")
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_xhtml_fragments=True
    )
    fragment = next(
        block.xhtml_fragment for block in extraction.blocks if block.tag_name == "p"
    )
    assert fragment.text == "A\xa0B & C"
    assert visible_text(fragment.xhtml) == fragment.text


def test_xhtml_disallowed_attributes_produce_diagnostics(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(
        epub_path, '<p><span onclick="evil()" class="ok">text</span></p>'
    )
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_xhtml_fragments=True
    )
    block = next(block for block in extraction.blocks if block.tag_name == "p")
    assert "onclick" not in block.xhtml_fragment.xhtml
    assert 'class="ok"' in block.xhtml_fragment.xhtml
    assert any(
        d.code == "xhtml_fragment_disallowed_attr" for d in extraction.diagnostics
    )


def test_xhtml_default_json_omits_fragments(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(epub_path, "<p>A <em>small</em> test.</p>")
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_segments=True, include_xhtml_fragments=True
    )
    assert "xhtml_fragment" not in extraction.to_json(
        include_runs=True, include_segments=True
    )


def test_xhtml_fragments_serialize_without_runs(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(epub_path, "<p>A <em>small</em> test.</p>")
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_xhtml_fragments=True
    )
    decoded = json.loads(
        extraction.to_json(include_runs=False, include_xhtml_fragments=True)
    )
    assert "runs" not in decoded["blocks"][0]
    assert decoded["blocks"][0]["xhtml_fragment"]["xhtml"] == "A <em>small</em> test."


def test_xhtml_segment_starts_before_inline_and_ends_inside(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(epub_path, "<p>Start <em>middle. end</em></p>")
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_segments=True, include_xhtml_fragments=True
    )
    segment = extraction.segments[0]
    assert segment.text == "Start middle."
    assert segment.xhtml_fragment.xhtml == "Start <em>middle.</em>"


def test_xhtml_segment_starts_inside_inline_and_ends_after(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(epub_path, "<p><em>Start. middle</em> end.</p>")
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_segments=True, include_xhtml_fragments=True
    )
    segment = next(
        segment for segment in extraction.segments if segment.text == "middle end."
    )
    assert segment.xhtml_fragment.xhtml == "<em>middle</em> end."


def test_xhtml_void_inline_tags_are_deterministic(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(epub_path, "<p>A<br/>B<wbr/>C</p>")
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_xhtml_fragments=True
    )
    fragment = next(
        block.xhtml_fragment for block in extraction.blocks if block.tag_name == "p"
    )
    assert fragment.xhtml == "A<br/>B<wbr/>C"
    assert visible_text(fragment.xhtml) == fragment.text


def test_xhtml_disallowed_tags_produce_diagnostics(tmp_path):
    epub_path = tmp_path / "book.epub"
    make_epub_with_body(epub_path, "<p>A <script>alert(1)</script> B</p>")
    extraction = EPUBParser(str(epub_path)).extract_structured(
        include_xhtml_fragments=True
    )
    fragment = next(
        block.xhtml_fragment for block in extraction.blocks if block.tag_name == "p"
    )
    assert "script" not in fragment.xhtml
    assert not any("<script" in fragment.xhtml for _ in [0])
    assert any(
        d.code == "xhtml_fragment_disallowed_tag" for d in extraction.diagnostics
    )
