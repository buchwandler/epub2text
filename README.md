[![PyPI - Version](https://img.shields.io/pypi/v/epub2text)](https://pypi.org/project/epub2text/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/epub2text)
![PyPI - Downloads](https://img.shields.io/pypi/dm/epub2text)
[![codecov](https://codecov.io/gh/holgern/epub2text/graph/badge.svg?token=iCHXwbjAXG)](https://codecov.io/gh/holgern/epub2text)

# epub2text

A niche CLI tool to extract text from EPUB files with smart cleaning capabilities.

## Features

- **Smart Navigation Parsing**: Supports both EPUB3 (NAV HTML) and EPUB2 (NCX)
  navigation formats
- **Multiple Extraction Modes**:
  - Chapter-based extraction with selective range support
  - Page-based extraction (using EPUB page-list or synthetic pages)
  - Project Gutenberg format output with proper formatting
- **Interactive Terminal Reader**:
  - Vim-style navigation (j/k, Space/b, n/p for chapters)
  - Bookmark support with automatic resume
  - Adjustable page size and content width
- **Flexible Output Formatting**:
  - One paragraph per line with customizable separators
  - One sentence per line using spaCy NLP
  - One clause per line (split at commas, semicolons)
  - Automatic line splitting at clause boundaries for long lines
- **Smart Text Cleaning**:
  - Remove bracketed footnotes (`[1]`, `[42]`)
  - Remove page numbers (standalone, at line ends, with dashes)
  - Normalize whitespace and paragraph breaks
  - Preserve ordered lists with proper numbering
  - Optional front matter/TOC filtering
- **Full Dublin Core Metadata**: Extract all EPUB metadata fields
- **Rich Interactive UI**: Beautiful terminal output with tables and tree views
- **Pipe-Friendly**: Works as both CLI tool and Python library
- **Nested Chapter Support**: Handles hierarchical chapter structures
- **URL Support**: Extract text directly from EPUB files hosted online

## Structured extraction for downstream tooling

For downstream tools that need stable source mapping, `epub2text` provides a read-only
structured extraction API. It exposes package metadata, spine source documents,
navigation entries, text blocks, inline markup runs, entity runs, optional segments, and
diagnostics without changing the normal plain-text reader APIs.

```python
from epub2text import EPUBParser

parser = EPUBParser("book.epub")
extraction = parser.extract_structured(include_segments=True)
json_payload = extraction.to_json(include_raw=False, indent=2)
```

Structured extraction is not an EPUB writer. It does not rebuild EPUB ZIP files, apply
translated text, write OPF/NAV/NCX files, or replace XHTML content. See
`docs/structured_extraction.md` for the data model, offset semantics, diagnostics,
strict mode, and downstream consumer guidance.

Set `include_xhtml_fragments=True` on `extract_structured()` or
`extract_epub_structure()` to attach sanitized inline XHTML fragments to blocks, and to
segments when `include_segments=True`. Fragment output is opt-in and `to_json()` omits
`xhtml_fragment` unless `include_xhtml_fragments=True` is passed.

Set `include_markdown_fragments=True` to attach Markdown translations of the same inline
structure to blocks and, when `include_segments=True`, to segments. Markdown fragments
are a lossy, readable representation rendered from structured runs. Use `xhtml_fragment`
when exact inline semantics are required. Pass `include_markdown_fragments=True` to
`to_dict()` or `to_json()` to serialize `markdown_fragment`.

```python
from epub2text import EPUBParser

parser = EPUBParser("book.epub")
extraction = parser.extract_structured(
    include_segments=True,
    include_xhtml_fragments=True,
    include_markdown_fragments=True,
    markdown_flavor="gfm",
)
```

```bash
epub2text extract-structure book.epub --xhtml-fragments -o structure.json
epub2text extract-structure book.epub --markdown-fragments --markdown-flavor gfm -o structure.json
epub2text extract-structure book.epub --segments sentence --xhtml-fragments --markdown-fragments -o structure.json
```

## Installation

```bash
pip install epub2text
```

For better HTML parsing performance (optional):

```bash
pip install epub2text[lxml]
```

For sentence-level formatting (requires spaCy):

```bash
pip install epub2text[sentences]
python -m spacy download en_core_web_sm
```

Note: Sentence formatting uses the `phrasplit` library which depends on spaCy.

### Development Installation

```bash
git clone https://github.com/buchwandler/epub2text
cd epub2text
pip install -e .
```

## Usage

### Command Line Interface

#### List Chapters

Display all chapters in an EPUB file:

```bash
# Table format (default)
epub2text list book.epub

# Tree format (shows hierarchy)
epub2text list book.epub --format tree
```

#### Extract Text by Chapters

Extract all chapters:

```bash
# To stdout
epub2text extract book.epub

# To file
epub2text extract book.epub -o output.txt
```

Extract specific chapters by range:

```bash
# Single chapter
epub2text extract book.epub -c 1

# Multiple chapters
epub2text extract book.epub -c 1,3,5

# Chapter range
epub2text extract book.epub -c 1-5

# Complex range
epub2text extract book.epub -c 1-5,7,9-12 -o selected.txt
```

Interactive chapter selection:

```bash
epub2text extract book.epub --interactive
```

**Output Formatting:**

```bash
# One line per paragraph
epub2text extract book.epub --paragraphs

# One line per sentence (requires spaCy)
epub2text extract book.epub --sentences

# One line per clause (split at commas, semicolons)
epub2text extract book.epub --comma

# Combine sentence and clause splitting
epub2text extract book.epub --sentences --comma

# Split long lines at clause boundaries
epub2text extract book.epub --max-length 80

# Use empty lines between paragraphs
epub2text extract book.epub --empty-lines

# Custom paragraph separator
epub2text extract book.epub --separator "\t"
```

**Text Cleaning Options:**

```bash
# Disable all cleaning (raw output)
epub2text extract book.epub --raw

# Keep bracketed footnotes like [1]
epub2text extract book.epub --keep-footnotes

# Keep page numbers
epub2text extract book.epub --keep-page-numbers

# Hide chapter markers
epub2text extract book.epub --no-markers
```

**Output Control:**

```bash
# Skip first 10 lines
epub2text extract book.epub --offset 10

# Limit to 100 lines
epub2text extract book.epub --limit 100

# Add line numbers
epub2text extract book.epub --line-numbers
```

#### Extract Text by Pages

Extract content organized by pages instead of chapters:

```bash
# Extract all pages (uses EPUB page-list if available, otherwise generates synthetic pages)
epub2text extract-pages book.epub

# Extract specific page range
epub2text extract-pages book.epub --pages 1-10

# Generate synthetic pages with custom size (characters)
epub2text extract-pages book.epub --page-size 2000

# Use word count for synthetic pages
epub2text extract-pages book.epub --use-words --page-size 350

# Show front matter (TOC, acknowledgements, etc.)
epub2text extract-pages book.epub --show-front-matter

# Keep duplicate chapter titles in pages
epub2text extract-pages book.epub --keep-duplicate-titles
```

#### List Pages

View all pages in an EPUB:

```bash
# List pages (shows EPUB page-list or generates synthetic pages)
epub2text pages book.epub

# Customize synthetic page size
epub2text pages book.epub --page-size 2000 --use-words
```

#### Extract in Project Gutenberg Format

Generate text in Project Gutenberg format with proper headers and formatting:

```bash
# Extract complete book in Gutenberg format
epub2text extract-gutenberg book.epub

# Save to specific file
epub2text extract-gutenberg book.epub -o output.txt

# Extract specific chapters in Gutenberg format
epub2text extract-gutenberg book.epub --chapters 1-10

# Interactive chapter selection
epub2text extract-gutenberg book.epub --interactive
```

Features:

- Project Gutenberg-style header with metadata
- Table of Contents
- Two spaces after sentences and colons
- 72-character line wrapping
- Proper chapter formatting

#### Interactive Reader

Read EPUB files directly in your terminal with vim-style navigation:

```bash
# Start reading from the beginning
epub2text read book.epub

# Resume from last bookmark
epub2text read book.epub --resume

# Start at specific chapter
epub2text read book.epub --chapter 5

# Start at specific line
epub2text read book.epub --line 100

# Format as sentences while reading
epub2text read book.epub --sentences

# Format as clauses
epub2text read book.epub --comma

# Set maximum content width for better readability
epub2text read book.epub --width 80
```

**Navigation Keys:**

- `j`/`↓` - Scroll down one line
- `k`/`↑` - Scroll up one line
- `Space`/`PgDn` - Next page
- `b`/`PgUp` - Previous page
- `n` - Next chapter
- `p` - Previous chapter
- `g`/`Home` - Go to beginning
- `G`/`End` - Go to end
- `m` - Save bookmark
- `'` - Jump to bookmark
- `h`/`?` - Show help
- `q`/`Esc` - Quit

#### Show Metadata

Display EPUB metadata and statistics:

```bash
# Panel format (default)
epub2text info book.epub

# Table format
epub2text info book.epub --format table

# JSON format (for scripting)
epub2text info book.epub --format json
```

### Python Library

Use epub2text as a library in your Python code:

#### Basic Usage

```python
from epub2text import EPUBParser

# Parse EPUB file (or URL)
parser = EPUBParser("book.epub")
# parser = EPUBParser("https://example.com/book.epub")  # URLs supported

# Get metadata
metadata = parser.get_metadata()
print(f"Title: {metadata.title}")
print(f"Authors: {', '.join(metadata.authors)}")
print(f"Language: {metadata.language}")
print(f"Identifier: {metadata.identifier}")

# Get all chapters
chapters = parser.get_chapters()
for chapter in chapters:
    print(f"{chapter.title}: {chapter.char_count:,} characters")

# Extract all chapters
full_text = parser.extract_chapters()

# Extract specific chapters
chapter_ids = [chapters[0].id, chapters[2].id]
selected_text = parser.extract_chapters(chapter_ids)
```

#### Working with Pages

```python
from epub2text import EPUBParser

parser = EPUBParser("book.epub")

# Check if EPUB has page-list navigation
if parser.has_page_list():
    print("EPUB contains original page numbers")

# Get pages (from page-list or generate synthetic pages)
pages = parser.get_pages(synthetic_page_size=2000, use_words=False)

for page in pages:
    print(f"Page {page.page_number}: {page.char_count} chars")
    print(f"  Source: {page.source.value}")
    print(f"  Chapter: {page.chapter_title}")

# Extract text organized by pages
page_text = parser.extract_pages(
    page_numbers=["1", "2", "3"],  # Specific pages
    deduplicate_chapter_titles=True,
    skip_toc=True  # Skip table of contents
)
```

#### Custom Text Cleaning

```python
from epub2text import EPUBParser, TextCleaner

parser = EPUBParser("book.epub")
text = parser.extract_chapters()

# Custom cleaning options
cleaner = TextCleaner(
    remove_footnotes=True,
    remove_page_numbers=True,
    normalize_whitespace=True,
    replace_single_newlines=True,
    preserve_single_newlines=False,
)
cleaned_text = cleaner.clean(text)
```

#### Text Formatting

```python
from epub2text import EPUBParser
from epub2text.formatters import (
    format_sentences,
    format_clauses,
    format_paragraphs,
    split_long_lines,
)

parser = EPUBParser("book.epub")
text = parser.extract_chapters()

# One sentence per line
formatted = format_sentences(text, separator="  ")

# One clause per line (split at commas, semicolons)
clause_formatted = format_clauses(text, separator="  ")

# Format paragraphs with custom separator
para_formatted = format_paragraphs(
    text,
    separator="  ",
    one_line_per_paragraph=True
)

# Split long lines at clause boundaries
split_text = split_long_lines(text, max_length=80)
```

#### Compatibility Function

```python
from epub2text import epub2txt

# Simple extraction (compatible with old epub2txt package)
text = epub2txt("book.epub")

# Get list of chapter texts
chapters = epub2txt("book.epub", outputlist=True)

# Disable cleaning
raw_text = epub2txt("book.epub", clean=False)

# Works with URLs
text = epub2txt("https://example.com/book.epub")
```

#### Bookmark Management

```python
from epub2text.bookmarks import BookmarkManager, Bookmark

# Create bookmark manager
manager = BookmarkManager()  # Uses ~/.epub2text/bookmarks.json

# Save bookmark
bookmark = Bookmark.create(
    chapter_index=3,
    line_offset=150,
    percentage=45.5,
    title="My Book Title"
)
manager.save("/path/to/book.epub", bookmark)

# Load bookmark
bookmark = manager.load("/path/to/book.epub")
if bookmark:
    print(f"Resume at {bookmark.percentage:.1f}%")

# List all bookmarks
all_bookmarks = manager.list_all()
```

## Smart Cleaning Features

The smart text cleaner applies the following transformations by default:

1. **Bracketed Footnotes**: Removes `[1]`, `[42]`, etc.
2. **Page Numbers**:
   - Standalone page numbers on their own line
   - Page numbers at the end of lines
   - Page numbers with dashes (e.g., `- 42 -`)
3. **Whitespace Normalization**:
   - Collapses multiple spaces into one
   - Standardizes paragraph breaks to double newlines
   - Optionally replaces single newlines with spaces
4. **Chapter Markers**: Removes internal metadata tags

## Chapter Format

Extracted text includes chapter titles with clear visual separation:

```
Chapter Title

Chapter text content here...



Next Chapter

More content...
```

The first chapter appears as `{title}\n\n{content}`, while subsequent chapters are
separated by four linebreaks before the title, then two linebreaks after the title.

Use `--no-markers` to hide chapter titles from the output.

## Requirements

- Python >= 3.9
- click >= 8.0.0
- rich >= 13.0.0
- ebooklib >= 0.18
- beautifulsoup4 >= 4.12.0
- defusedxml >= 0.7.1
- lxml >= 4.9.0 (optional, for better HTML parsing performance)
- phrasplit >= 0.1.0 (optional, for sentence/clause formatting, depends on spaCy)

## Technical Details

### EPUB Parsing Strategy

The parser uses a sophisticated navigation-based approach:

1. Loads EPUB using ebooklib
2. Finds navigation document (prefers NAV HTML, falls back to NCX)
3. Parses navigation structure recursively
4. Maps TOC entries to document positions using fragment IDs
5. Slices HTML content between navigation points
6. Extracts text using BeautifulSoup
7. Applies smart cleaning and normalization

### Navigation Support

- **EPUB3 NAV HTML**: Parses `<nav epub:type="toc">` with nested `<ol>/<li>` structures
- **EPUB2 NCX**: Parses `<navMap>` with `<navPoint>` elements
- **Fragment IDs**: Robust position detection using BeautifulSoup, regex, and string
  search
- **Nested Structures**: Handles hierarchical chapter organization

### Metadata Support

Full Dublin Core metadata extraction:

- Title
- Authors (creators)
- Contributors
- Publisher
- Publication Year
- Identifier (ISBN, UUID, etc.)
- Language
- Rights (copyright)
- Coverage
- Description

## Documentation

Full documentation is available at [Read the Docs](https://epub2text.readthedocs.io/).

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details

## Author

Holger Nahrstaedt

## See Also

- **abogen**: Full-featured audiobook generator with TTS support
- **epub2txt**: Simple EPUB to text converter (different project)
