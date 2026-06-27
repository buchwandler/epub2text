# Changelog

All notable changes to epub2text will be documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `get_chapters()` method now supports `include_text` parameter for metadata-only
  extraction
- Full Dublin Core metadata support: `identifier`, `language`, `contributors`, `rights`,
  `coverage`
- New `extract` command formatting options:

  - `--paragraphs, -p`: One line per paragraph
  - `--sentences, -s`: One sentence per line (requires spaCy)
  - `--max-length, -m N`: Split long lines at clause boundaries
  - `--separator TEXT`: Custom paragraph separator (default: two spaces)
  - `--empty-lines`: Use empty lines between paragraphs
  - `--offset N`: Skip first N lines of output
  - `--limit N`: Limit output to N lines
  - `--line-numbers, -n`: Add line numbers to output

- New `info` command `--format` option: `panel` (default), `table`, or `json`
- Ellipsis handling: `...` and `. . .` are no longer treated as sentence boundaries
- Comprehensive test suite for metadata and formatters

### Changed

- **BREAKING**: Chapter format changed from `<<CHAPTER: Title>>` to clean separation
  with newlines

  - First chapter: `{title}\n\n{content}`
  - Subsequent chapters: `\n\n\n\n{title}\n\n{content}`
  - Four linebreaks before chapter title, two linebreaks after
  - More readable and natural text output

- Refactored `extract` command with cleaner, more intuitive options
- Improved `get_metadata()` function with reduced complexity
- Default paragraph separator changed from newlines to two-space prefix

### Removed

- Deprecated `--format-style` option (replaced by `--paragraphs`, `--sentences`)
- Deprecated `--no-clean` option (replaced by `--raw`)
- Deprecated `--no-chapter-titles` option (replaced by `--no-markers`)
- Deprecated `--no-empty-lines` option (default behavior now uses separators)

## [0.1.0] - 2025-01-01

### Added

- Initial release
- EPUB parsing with NAV HTML (EPUB3) and NCX (EPUB2) support
- Chapter listing with table and tree formats
- Text extraction with chapter selection
- Smart text cleaning (footnotes, page numbers, whitespace)
- Rich terminal UI with progress indicators
- Python library API
