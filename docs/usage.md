# Usage Guide

epub2text provides several commands for working with EPUB files: `list`, `extract`,
`extract-pages`, `extract-gutenberg`, `pages`, `read`, and `info`.

## List Chapters

Display all chapters in an EPUB file:

```bash
# Table format (default)
epub2text list book.epub

# Tree format (shows hierarchy)
epub2text list book.epub --format tree
```

The table format shows chapter numbers, titles, character counts, and nesting levels.
The tree format displays the hierarchical structure of nested chapters.

## Extract Text

### Extract by Chapters

#### Basic Extraction

Extract all chapters to stdout:

```bash
epub2text extract book.epub
```

Extract to a file:

```bash
epub2text extract book.epub -o output.txt
```

#### Chapter Selection

Extract specific chapters by number:

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

#### Output Formatting

**Paragraph Mode** (`-p, --paragraphs`): One line per paragraph:

```bash
epub2text extract book.epub --paragraphs
```

**Sentence Mode** (`-s, --sentences`): One line per sentence (requires phrasplit/spaCy):

```bash
epub2text extract book.epub --sentences
```

**Clause Mode** (`--comma`): One line per clause (split at commas, semicolons):

```bash
epub2text extract book.epub --comma
```

**Combined Modes**: Combine sentence and clause splitting:

```bash
epub2text extract book.epub --sentences --comma
```

**Max Line Length** (`-m, --max-length`): Split long lines at clause boundaries:

```bash
epub2text extract book.epub --max-length 80
```

**Paragraph Separators**:

By default, paragraphs are separated by two spaces at the start of each new paragraph.
You can customize this behavior:

```bash
# Use empty lines between paragraphs
epub2text extract book.epub --empty-lines

# Custom separator (e.g., tab)
epub2text extract book.epub --separator "\\t"

# No separator
epub2text extract book.epub --separator ""
```

#### Text Cleaning Options

By default, epub2text applies smart text cleaning. You can disable or customize it:

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

#### Output Control

Control which lines are output:

```bash
# Skip first 10 lines
epub2text extract book.epub --offset 10

# Limit to 100 lines
epub2text extract book.epub --limit 100

# Add line numbers
epub2text extract book.epub --line-numbers
```

#### Language Model

For sentence-level formatting, you can specify a different spaCy language model:

```bash
# Use German language model
epub2text extract book.epub --sentences --language-model de_core_news_sm
```

### Extract by Pages

Extract content organized by pages instead of chapters:

```bash
# Extract all pages (uses EPUB page-list if available, otherwise synthetic)
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

**Page-based extraction features:**

- Uses EPUB page-list navigation when available (original print book pages)
- Generates synthetic pages at sentence boundaries when page-list not available
- Automatically filters table of contents and front matter by default
- Organizes output by chapters with page markers (`<<PAGE: N>>`)
- Supports all text cleaning options (`--raw`, `--keep-footnotes`, etc.)

### Extract in Project Gutenberg Format

Generate text in Project Gutenberg format with proper headers and formatting:

```bash
# Extract complete book in Gutenberg format
epub2text extract-gutenberg book.epub

# Save to specific file (default: {book-title}.txt)
epub2text extract-gutenberg book.epub -o output.txt

# Extract specific chapters
epub2text extract-gutenberg book.epub --chapters 1-10

# Interactive chapter selection
epub2text extract-gutenberg book.epub --interactive
```

**Features of Gutenberg format:**

- Project Gutenberg-style header with metadata
- Table of Contents
- Two spaces after sentences and colons
- 72-character line wrapping
- Proper chapter formatting with uppercase titles
- Automatic filtering of front matter chapters

## List Pages

View all pages in an EPUB file:

```bash
# List pages (shows EPUB page-list or generates synthetic pages)
epub2text pages book.epub

# Customize synthetic page size (in characters)
epub2text pages book.epub --page-size 2000

# Use word count instead of character count
epub2text pages book.epub --use-words --page-size 350
```

The `pages` command displays:

- Page numbers (from page-list or generated: "1", "2", "3", ...)
- Character count per page
- Source type (print page-list or synthetic)
- Chapter assignment for each page
- Total character count

## Interactive Reader

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

# Hide header or footer
epub2text read book.epub --no-header --no-footer
```

**Navigation Keys:**

- `j` / `↓` - Scroll down one line
- `k` / `↑` - Scroll up one line
- `Space` / `PgDn` - Next page
- `b` / `PgUp` - Previous page
- `n` - Next chapter
- `p` - Previous chapter
- `g` / `Home` - Go to beginning
- `G` / `End` - Go to end
- `m` - Save bookmark
- `'` - Jump to bookmark
- `h` / `?` - Show help
- `q` / `Esc` - Quit

**Features:**

- Automatic bookmark management (saved to `~/.epub2text/bookmarks.json`)
- Custom bookmark file support (`--bookmark-file`)
- Configurable page size (`--page-size`)
- Adjustable content width for better readability (`--width`)
- Support for all text formatting options (`--sentences`, `--comma`, `--paragraphs`)
- Full text cleaning options (`--raw`, `--keep-footnotes`, etc.)

## Show Metadata

Display EPUB metadata and statistics:

```bash
# Panel format (default)
epub2text info book.epub

# Table format
epub2text info book.epub --format table

# JSON format (for scripting)
epub2text info book.epub --format json
```

The `info` command displays:

- Title
- Authors
- Contributors
- Publisher
- Publication Year
- Identifier (ISBN, UUID, etc.)
- Language
- Rights (copyright)
- Coverage
- Description
- Chapter count
- Page count (from page-list or estimated)
- Total character count

## Chapter and Page Markers

### Chapter Markers

Extracted text includes chapter titles with clear visual separation:

```text
Chapter Title

Chapter text content here...


Next Chapter

More content...
```

The first chapter appears as `{title}\n\n{content}`, while subsequent chapters are
separated by four linebreaks before the title, then two linebreaks after the title.

Use `--no-markers` to hide chapter titles from the output.

### Page Markers

When using `extract-pages`, pages are marked with the format `<<PAGE: N>>`:

```text
Chapter Title

<<PAGE: 1>>

First page content...

<<PAGE: 2>>

Second page content...
```

Use `--no-markers` to hide these page markers from the output.

## Examples

Extract a book for text-to-speech processing:

```bash
# One sentence per line, suitable for TTS
epub2text extract book.epub --sentences -o book.txt

# One clause per line (even better for TTS)
epub2text extract book.epub --comma -o book.txt
```

Create a clean plain text version:

```bash
# Paragraphs with empty lines, no markers
epub2text extract book.epub --paragraphs --empty-lines --no-markers -o book.txt
```

Extract specific chapters with line length limit:

```bash
# Chapters 1-5 with max 100 chars per line
epub2text extract book.epub -c 1-5 --max-length 100 -o excerpt.txt
```

Extract by page numbers:

```bash
# Extract pages 1-20 from EPUB page-list
epub2text extract-pages book.epub --pages 1-20 -o chapter1.txt

# Generate synthetic pages and extract first 10
epub2text extract-pages book.epub --page-size 500 --pages 1-10 -o sample.txt
```

Create a Project Gutenberg-style text file:

```bash
# Complete book in Gutenberg format
epub2text extract-gutenberg book.epub

# Specific chapters only
epub2text extract-gutenberg book.epub --chapters 5-10 -o excerpt.txt
```

Interactive reading:

```bash
# Start reading and automatically resume later
epub2text read book.epub
# ... quit and come back later ...
epub2text read book.epub --resume
```

Get metadata as JSON for scripting:

```bash
epub2text info book.epub --format json | jq '.title'
```
