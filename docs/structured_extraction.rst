Structured extraction
=====================

Structured extraction is the read-only EPUB inspection API for downstream tools
that need stable source mapping. It is separate from the plain-text reading APIs.
``epub2txt()`` and ``EPUBParser.extract_chapters()`` keep producing cleaned text
for readers, while ``EPUBParser.extract_structured()`` exposes package metadata,
spine source documents, navigation entries, text blocks, inline runs, segments,
and diagnostics.

Plain text versus structured extraction
---------------------------------------

Plain-text extraction may normalize whitespace, remove duplicate titles, inject
readable separators, or otherwise format content for humans. Structured
extraction does not perform those destructive reading transformations by
default. Block text is visible text only and does not contain internal placeholder
tokens such as ``__TAG_001__``.

No EPUB rebuilding
------------------

``epub2text`` only reports what text exists and where it came from. It does not
write EPUB files, rebuild ZIP packages, apply translations, write OPF/NAV/NCX
files, or replace XHTML text. Downstream projects that need writing should use a
separate writer package.

Data model overview
-------------------

The structured API uses dataclasses:

* ``EpubPackageInfo`` for package metadata, manifest items, and spine order.
* ``SourceDocument`` for decoded spine XHTML/HTML and raw-byte hashes.
* ``NavigationEntry`` for flattened, deterministic navigation entries.
* ``TextBlock`` for prose blocks with source ranges and visible text.
* ``TextRun``, ``InlineTagRun``, and ``EntityRun`` for ordered content runs.
* ``TextSegment`` for sentence, paragraph, or clause slices.
* ``Diagnostic`` for loss, fallback, and unresolved-reference reporting.

Offset semantics
----------------

Character offsets point into ``SourceDocument.text``. Byte offsets are included
when a char-to-byte map can be built for the detected encoding. For exact blocks,
``outer_char_start`` to ``outer_char_end`` slices the full source element and
``inner_char_start`` to ``inner_char_end`` slices the inner source. Text-bearing
runs join to exactly ``TextBlock.text``.

Diagnostics and strict mode
---------------------------

Diagnostics use severities ``info``, ``warning``, and ``error`` with stable codes
such as ``missing_nav``, ``unresolved_href``, ``unresolved_fragment``,
``encoding_fallback``, and ``offset_unavailable``. ``ExtractionPolicy`` includes
``strict_offsets`` for callers that want warning and error diagnostics to fail
closed.

JSON export example
-------------------

.. code-block:: python

   from epub2text import EPUBParser

   parser = EPUBParser("book.epub")
   extraction = parser.extract_structured(include_segments=True)
   data = extraction.to_json(include_raw=False, include_runs=True, indent=2)

The JSON export embeds schema ``epub2text.structured.v1`` and supports omitting
raw source text, runs, or segments for smaller output.

Downstream consumer notes
-------------------------

Downstream tools should consume block and segment IDs, preserve diagnostics and
schema version, and use source offsets from structured extraction instead of
inferring offsets from cleaned text. Consumers that require lossless rebuilding
should fail closed when diagnostics report non-lossless extraction.
