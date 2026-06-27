# epub2text Documentation

A niche CLI tool to extract text from EPUB files with smart cleaning capabilities.

```{toctree}
:maxdepth: 2
:caption: Contents:

installation
usage
api
changelog
```

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
- **Rich Interactive UI**: Beautiful terminal output with tables and tree views
- **Pipe-Friendly**: Works as both CLI tool and Python library
- **Nested Chapter Support**: Handles hierarchical chapter structures
- **Full Dublin Core Metadata**: Extract all EPUB metadata fields
- **URL Support**: Extract text directly from EPUB files hosted online

## Quick Start

Install epub2text:

```bash
pip install epub2text
```

Extract text from an EPUB file:

```bash
epub2text extract book.epub
```

Extract by pages:

```bash
epub2text extract-pages book.epub
```

List chapters:

```bash
epub2text list book.epub
```

List pages:

```bash
epub2text pages book.epub
```

Read interactively:

```bash
epub2text read book.epub
```

Show metadata:

```bash
epub2text info book.epub
```

# Indices and tables

- {ref}`genindex`
- {ref}`modindex`
- {ref}`search`
