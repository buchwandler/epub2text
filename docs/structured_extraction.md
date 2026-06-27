---
orphan: true
---

# Structured extraction

Structured extraction is the read-only EPUB inspection API for downstream tools that
need stable source mapping. It is separate from the plain-text reading APIs.
`epub2txt()` and `EPUBParser.extract_chapters()` keep producing cleaned text for
readers, while `EPUBParser.extract_structured()` exposes package metadata, spine source
documents, navigation entries, text blocks, inline runs, segments, and diagnostics.

## Plain text versus structured extraction

Plain-text extraction may normalize whitespace, remove duplicate titles, inject readable
separators, or otherwise format content for humans. Structured extraction does not
perform those destructive reading transformations by default. Block text is visible text
only and does not contain internal placeholder tokens such as `__TAG_001__`.

## No EPUB rebuilding

`epub2text` only reports what text exists and where it came from. It does not write EPUB
files, rebuild ZIP packages, apply translations, write OPF/NAV/NCX files, or replace
XHTML text. Downstream projects that need writing should use a separate writer package.

## Data model overview

The structured API uses dataclasses:

- `EpubPackageInfo` for package metadata, manifest items, and spine order.
- `SourceDocument` for decoded spine XHTML/HTML and raw-byte hashes.
- `NavigationEntry` for flattened, deterministic navigation entries.
- `TextBlock` for prose blocks with source ranges and visible text.
- `TextRun`, `InlineTagRun`, and `EntityRun` for ordered content runs.
- `TextSegment` for sentence, paragraph, or clause slices.
- `Diagnostic` for loss, fallback, and unresolved-reference reporting.
- `XhtmlFragment` for opt-in sanitized inline XHTML attached to blocks and segments.
- `MarkdownFragment` for opt-in Markdown translations of inline XHTML attached to blocks
  and segments.

## Offset semantics

Character offsets point into `SourceDocument.text`. Byte offsets are included when a
char-to-byte map can be built for the detected encoding. For exact blocks,
`outer_char_start` to `outer_char_end` slices the full source element and
`inner_char_start` to `inner_char_end` slices the inner source. Text-bearing runs join
to exactly `TextBlock.text`.

## XHTML fragments

Call `EPUBParser.extract_structured(include_xhtml_fragments=True)` or
`extract_epub_structure(..., include_xhtml_fragments=True)` to attach `xhtml_fragment`
to each `TextBlock`. When `include_segments=True` is also set, each `TextSegment`
receives a fragment for its visible text range. Fragments are rendered from structured
runs, not by serializing BeautifulSoup. They preserve allowed inline tags such as `em`,
`strong`, `span`, `a`, `code`, `br`, and `wbr` while omitting block tags, scripts, and
event handlers. `XhtmlFragment.text` is the represented visible text and should match
the visible text of `XhtmlFragment.xhtml`.

The default policy keeps global safe attributes such as `class`, `id`, `lang`,
`xml:lang`, `dir`, `title`, and `epub:type`. Links may also keep `href`. Disallowed tags
or attributes produce diagnostics such as `xhtml_fragment_disallowed_tag` and
`xhtml_fragment_disallowed_attr`. Unbalanced inline markup, opaque inline preservation,
and visible-text mismatches use stable fragment diagnostic codes. `strict_offsets=True`
fails closed on warning or error diagnostics, including fragment diagnostics.

JSON export omits `xhtml_fragment` by default, even if fragments were generated. Pass
`include_xhtml_fragments=True` to `to_dict()` or `to_json()` to include generated
fragments. This keeps the default payload compatible and compact.

## Markdown fragments

Call `EPUBParser.extract_structured(include_markdown_fragments=True)` or
`extract_epub_structure(..., include_markdown_fragments=True)` to attach
`markdown_fragment` to each `TextBlock`. When `include_segments=True` is also set, each
`TextSegment` receives a fragment for its visible text range. Markdown fragments are
rendered from structured runs, not from serialized XHTML.

`MarkdownFragment.markdown` is a readable, lossy representation of the same visible text
range as `xhtml_fragment`. The default flavor is `commonmark` and callers may select
`gfm` with `markdown_flavor="gfm"` or the CLI `--markdown-flavor` option. The first
renderer preserves emphasis, strong text, safe inline links, code-like spans, and hard
line breaks. Unsupported or unsafe inline tags unwrap or drop with diagnostics such as
`markdown_fragment_no_markdown_equivalent`, `markdown_fragment_invalid_href`, and
`markdown_fragment_disallowed_tag`.

Raw HTML fallback is disabled by default. Treat Markdown fragments as downstream reading
aids for translation, TTS, or agent workflows, not as a lossless EPUB rewrite format.
Use `xhtml_fragment` when exact inline semantics are required.

JSON export omits `markdown_fragment` by default, even if fragments were generated. Pass
`include_markdown_fragments=True` to `to_dict()` or `to_json()` to include generated
fragments.

## CLI examples

```bash
epub2text extract-structure book.epub --xhtml-fragments -o structure.json
epub2text extract-structure book.epub --markdown-fragments --markdown-flavor gfm -o structure.json
epub2text extract-structure book.epub --segments sentence --xhtml-fragments --markdown-fragments -o structure.json
```

## Diagnostics and strict mode

Diagnostics use severities `info`, `warning`, and `error` with stable codes such as
`missing_nav`, `unresolved_href`, `unresolved_fragment`, `encoding_fallback`, and
`offset_unavailable`. `ExtractionPolicy` includes `strict_offsets` for callers that want
warning and error diagnostics to fail closed.

## JSON export example

```python
from epub2text import EPUBParser

parser = EPUBParser("book.epub")
extraction = parser.extract_structured(include_segments=True)
data = extraction.to_json(include_raw=False, include_runs=True, indent=2)
```

The JSON export embeds schema `epub2text.structured.v1` and supports omitting raw source
text, runs, or segments for smaller output.

## Downstream consumer notes

Downstream tools should consume block and segment IDs, preserve diagnostics and schema
version, and use source offsets from structured extraction instead of inferring offsets
from cleaned text. Consumers that require lossless rebuilding should fail closed when
diagnostics report non-lossless extraction.
