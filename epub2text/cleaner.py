"""Text cleaning utilities extracted from abogen."""

import re

# Pre-compile frequently used regex patterns for better performance
_BRACKETED_NUMBERS_PATTERN = re.compile(r"\[\s*\d+\s*\]")
_BRACKETED_PAGE_NUMBERS_PATTERN = re.compile(r"^\s*\[\s*\d+\s*\]\s*$", re.MULTILINE)
_STANDALONE_PAGE_NUMBERS_PATTERN = re.compile(r"^\s*\d+\s*$", re.MULTILINE)
_PAGE_NUMBERS_AT_END_PATTERN = re.compile(r"\s+\d+\s*$", re.MULTILINE)
_PAGE_NUMBERS_WITH_DASH_PATTERN = re.compile(
    r"\s+[-–—]\s*\d+\s*[-–—]?\s*$", re.MULTILINE
)
_WHITESPACE_PATTERN = re.compile(r"[^\S\n]+")
_MULTIPLE_NEWLINES_PATTERN = re.compile(r"\n{3,}")
_SINGLE_NEWLINE_PATTERN = re.compile(r"(?<!\n)\n(?!\n)")
_CHAPTER_MARKER_PATTERN = re.compile(r"<<CHAPTER_MARKER:[^>]*>>")
_METADATA_TAG_PATTERN = re.compile(r"<<METADATA_[^:]+:[^>]*>>")
# Pattern to match chapter and page markers used in extract_pages/extract_chapters
_PAGE_CHAPTER_MARKER_PATTERN = re.compile(r"<<(?:CHAPTER|PAGE):[^>]*>>")


# Common abbreviations that should NOT get double spacing after period
ABBREVIATIONS = {
    "Mr",
    "Mrs",
    "Ms",
    "Dr",
    "Prof",
    "Sr",
    "Jr",
    "vs",
    "etc",
    "i.e",
    "e.g",
    "Ph.D",
    "M.D",
    "B.A",
    "M.A",
    "D.C.L",
    "L.L.D",
    "F.R.S",
    "St",
    "Rev",
    "Hon",
    "Messrs",
    "Mmes",
    "Msgr",
    "U.S",
    "U.K",
    "A.M",
    "P.M",
    "a.m",
    "p.m",
}


class TextCleaner:
    """Smart text cleaning with configurable options."""

    def __init__(
        self,
        remove_page_numbers: bool = True,
        remove_footnotes: bool = True,
        replace_single_newlines: bool = True,
        normalize_whitespace: bool = True,
        preserve_single_newlines: bool = False,
    ):
        """Initialize text cleaner with options.

        :param remove_page_numbers: Remove standalone and end-of-line page numbers.
        :param remove_footnotes: Remove bracketed footnote markers like ``[1]``.
        :param replace_single_newlines: Replace single newlines with spaces
            while preserving paragraphs.
        :param normalize_whitespace: Collapse multiple spaces to a single space.
        :param preserve_single_newlines: Keep single newlines as paragraph separators.
            This overrides ``replace_single_newlines``.
        """
        self.remove_page_numbers = remove_page_numbers
        self.remove_footnotes = remove_footnotes
        self.replace_single_newlines = replace_single_newlines
        self.normalize_whitespace = normalize_whitespace
        self.preserve_single_newlines = preserve_single_newlines

    def clean(self, text: str) -> str:
        """Clean text with configured options.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        # Protect chapter and page markers by temporarily replacing them
        markers = {}
        marker_count = [0]

        def save_marker(match: re.Match[str]) -> str:
            placeholder = f"___MARKER_{marker_count[0]}___"
            markers[placeholder] = match.group(0)
            marker_count[0] += 1
            return placeholder

        text = _PAGE_CHAPTER_MARKER_PATTERN.sub(save_marker, text)

        # Remove metadata tags
        text = _METADATA_TAG_PATTERN.sub("", text)

        # Remove page numbers and footnotes if requested
        if self.remove_page_numbers:
            text = _BRACKETED_PAGE_NUMBERS_PATTERN.sub("", text)
            text = _STANDALONE_PAGE_NUMBERS_PATTERN.sub("", text)
            text = _PAGE_NUMBERS_AT_END_PATTERN.sub("", text)
            text = _PAGE_NUMBERS_WITH_DASH_PATTERN.sub("", text)

        if self.remove_footnotes:
            text = _BRACKETED_NUMBERS_PATTERN.sub("", text)

        # Normalize whitespace
        if self.normalize_whitespace:
            # Collapse all whitespace (excluding newlines) into single spaces per line
            lines = [
                _WHITESPACE_PATTERN.sub(" ", line).strip() for line in text.splitlines()
            ]
            text = "\n".join(lines)

            # Standardize paragraph breaks (multiple newlines become exactly two)
            # Unless preserve_single_newlines is True (for compact format)
            if not self.preserve_single_newlines:
                text = _MULTIPLE_NEWLINES_PATTERN.sub("\n\n", text).strip()
            else:
                # For compact format, collapse multiple newlines to single
                text = _MULTIPLE_NEWLINES_PATTERN.sub("\n", text).strip()

        # Replace single newlines with spaces, but preserve double newlines
        # Unless preserve_single_newlines is True (for compact format)
        if self.replace_single_newlines and not self.preserve_single_newlines:
            text = _SINGLE_NEWLINE_PATTERN.sub(" ", text)

        # Restore protected markers
        for placeholder, marker in markers.items():
            text = text.replace(placeholder, marker)

        return text

    def apply_gutenberg_spacing(self, text: str) -> str:
        """Apply Gutenberg Project formatting: two spaces after sentences and colons.

        Args:
            text: Text to format

        Returns:
            Text with Gutenberg spacing
        """
        try:
            from phrasplit import split_sentences
        except ImportError:
            # Fallback to simple regex if phrasplit not available
            return self._apply_gutenberg_spacing_simple(text)

        # Process text paragraph by paragraph to preserve structure
        paragraphs = text.split("\n\n")
        result_paragraphs = []

        for para in paragraphs:
            if not para.strip():
                result_paragraphs.append(para)
                continue

            # Split paragraph into sentences
            sentences = split_sentences(para)

            # Join sentences with double spaces
            formatted = "  ".join(sentences)
            result_paragraphs.append(formatted)

        # Rejoin paragraphs
        result = "\n\n".join(result_paragraphs)

        # Two spaces after ALL colons (apply after sentence joining)
        result = re.sub(r":\s+", r":  ", result)

        return result

    def _apply_gutenberg_spacing_simple(self, text: str) -> str:
        """Fallback method for Gutenberg spacing without phrasplit.

        Args:
            text: Text to format

        Returns:
            Text with Gutenberg spacing
        """
        # Protect abbreviations
        abbrev_map = {}
        abbrev_counter = [0]

        def protect_abbrev(match: re.Match[str]) -> str:
            placeholder = f"__ABBREV_{abbrev_counter[0]}__"
            abbrev_map[placeholder] = match.group(0)
            abbrev_counter[0] += 1
            return placeholder

        for abbr in ABBREVIATIONS:
            text = re.sub(
                rf"\b{re.escape(abbr)}\.\s", protect_abbrev, text, flags=re.IGNORECASE
            )

        # Two spaces after colons
        text = re.sub(r":\s+", r":  ", text)

        # Two spaces after sentence-ending punctuation
        text = re.sub(r'\.\s+([A-Z"\'])', r".  \1", text)
        text = re.sub(r'([!?])\s+([A-Z"\'])', r"\1  \2", text)

        # Restore abbreviations
        for placeholder, original in abbrev_map.items():
            text = text.replace(placeholder, original)

        # Clean up triple+ spaces
        text = re.sub(r" {3,}", "  ", text)

        return text

    def calculate_length(self, text: str) -> int:
        """Calculate text length excluding chapter markers and metadata.

        Args:
            text: Text to measure

        Returns:
            Character count
        """
        # Ignore chapter markers and metadata patterns
        text = _CHAPTER_MARKER_PATTERN.sub("", text)
        text = _METADATA_TAG_PATTERN.sub("", text)
        # Ignore newlines and leading/trailing spaces
        text = text.replace("\n", "").strip()
        return len(text)


def clean_text(
    text: str,
    remove_page_numbers: bool = True,
    remove_footnotes: bool = True,
    replace_single_newlines: bool = True,
    normalize_whitespace: bool = True,
    preserve_single_newlines: bool = False,
) -> str:
    """Clean text with smart options (convenience function).

    Args:
        text: Raw text to clean
        remove_page_numbers: Remove standalone and end-of-line page numbers
        remove_footnotes: Remove bracketed footnote markers like [1]
        replace_single_newlines: Replace single newlines with spaces
        normalize_whitespace: Collapse multiple spaces to single space
        preserve_single_newlines: Keep single newlines as paragraph separators

    Returns:
        Cleaned text
    """
    cleaner = TextCleaner(
        remove_page_numbers=remove_page_numbers,
        remove_footnotes=remove_footnotes,
        replace_single_newlines=replace_single_newlines,
        normalize_whitespace=normalize_whitespace,
        preserve_single_newlines=preserve_single_newlines,
    )
    return cleaner.clean(text)


def calculate_text_length(text: str) -> int:
    """Calculate text length excluding markers and metadata.

    Args:
        text: Text to measure

    Returns:
        Character count
    """
    cleaner = TextCleaner()
    return cleaner.calculate_length(text)
