"""Text formatting utilities for different output styles."""

import re

from phrasplit import (
    split_clauses,
    split_paragraphs,
    split_sentences,
)
from phrasplit import (
    split_long_lines as _phrasplit_split_long_lines,
)


def collapse_paragraph(paragraph: str) -> str:
    """
    Collapse a paragraph to a single line.

    Replaces internal newlines with spaces.

    Args:
        paragraph: Single paragraph text

    Returns:
        Paragraph as single line
    """
    # Replace newlines with spaces, collapse multiple spaces
    result = re.sub(r"\s*\n\s*", " ", paragraph)
    result = re.sub(r"  +", " ", result)
    return result.strip()


def format_paragraphs(
    text: str,
    separator: str = "  ",
    one_line_per_paragraph: bool = False,
) -> str:
    """
    Format text with paragraph separators.

    This function works without phrasplit.

    Args:
        text: Input text with paragraph breaks (double newlines)
        separator: String to prepend to new paragraphs (default: "  " two spaces)
        one_line_per_paragraph: If True, collapse each paragraph to single line

    Returns:
        Formatted text with separator at start of each new paragraph.
        Chapter titles (lines preceded by 4+ newlines) are preserved.
    """
    paragraphs = split_paragraphs(text)

    if not paragraphs:
        return ""

    result_parts = []
    for i, para in enumerate(paragraphs):
        if one_line_per_paragraph:
            para = collapse_paragraph(para)

        if i == 0:
            # First paragraph: no separator
            result_parts.append(para)
        else:
            # Subsequent paragraphs: add separator at start
            # Don't add separator to chapter titles (they are standalone)
            # Chapter titles are identified by checking if they're very short
            # and don't end with sentence-ending punctuation
            is_likely_chapter_title = (
                len(para) < 100
                and not para.rstrip().endswith((".", "!", "?", '"', "'"))
                and "\n" not in para
            )

            if separator and not is_likely_chapter_title:
                # Add separator to each line of the paragraph
                lines = para.split("\n")
                lines[0] = separator + lines[0]
                para = "\n".join(lines)
            result_parts.append(para)

    return "\n".join(result_parts)


def format_sentences(
    text: str,
    separator: str = "  ",
    language_model: str = "en_core_web_sm",
) -> str:
    """
    Format text with one sentence per line.

    Args:
        text: Input text with paragraph breaks
        separator: String to prepend at paragraph boundaries (default: "  ")
        language_model: spaCy language model to use

    Returns:
        Text with one sentence per line, separator at paragraph boundaries.
        Chapter titles are preserved.
    """
    paragraphs = split_paragraphs(text)

    if not paragraphs:
        return ""

    result_lines: list[str] = []
    for i, para in enumerate(paragraphs):
        # Check if this is likely a chapter title
        # (short, no sentence-ending punctuation)
        is_likely_chapter_title = (
            len(para) < 100
            and not para.rstrip().endswith((".", "!", "?", '"', "'"))
            and "\n" not in para
        )

        if is_likely_chapter_title:
            result_lines.append(para)
            continue

        # Process paragraph into sentences using phrasplit
        sentences = split_sentences(para, language_model)

        if not sentences:
            continue

        # Add separator to first sentence if not first paragraph
        for j, sent in enumerate(sentences):
            if i > 0 and j == 0 and separator:
                result_lines.append(separator + sent)
            else:
                result_lines.append(sent)

    return "\n".join(result_lines)


def format_clauses(
    text: str,
    separator: str = "  ",
    language_model: str = "en_core_web_sm",
) -> str:
    """
    Format text with one clause per line (split at commas).

    Uses spaCy for sentence detection, then splits each sentence at commas.
    The comma stays at the end of each clause, creating natural pause points
    for text-to-speech processing.

    Requires phrasplit to be installed.

    :param text: Input text with paragraph breaks.
    :param separator: String to prepend at paragraph boundaries. Default is two spaces.
    :param language_model: spaCy language model to use.
    :returns: Text with one clause per line, separator at paragraph boundaries.
        Chapter titles are preserved.

    Example::

        Input: "I do like coffee, and I like wine."
        Output:
            "I do like coffee,
            and I like wine."
    """

    paragraphs = split_paragraphs(text)

    if not paragraphs:
        return ""

    result_lines: list[str] = []
    for i, para in enumerate(paragraphs):
        # Check if this is likely a chapter title
        is_likely_chapter_title = (
            len(para) < 100
            and not para.rstrip().endswith((".", "!", "?", '"', "'"))
            and "\n" not in para
        )

        if is_likely_chapter_title:
            result_lines.append(para)
            continue

        # Process paragraph into clauses using phrasplit
        clauses = split_clauses(para, language_model)

        if not clauses:
            continue

        # Add separator to first clause if not first paragraph
        is_first_clause_in_para = True
        for clause in clauses:
            if i > 0 and is_first_clause_in_para and separator:
                result_lines.append(separator + clause)
            else:
                result_lines.append(clause)
            is_first_clause_in_para = False

    return "\n".join(result_lines)


def split_long_lines(
    text: str,
    max_length: int,
    separator: str = "  ",
    language_model: str = "en_core_web_sm",
) -> str:
    """
    Split lines exceeding max_length at clause/sentence boundaries.

    Strategy:
    1. First try to split at sentence boundaries
    2. If still too long, split at clause boundaries (commas, semicolons, etc.)
    3. If still too long, split at word boundaries

    Args:
        text: Input text (may already be formatted)
        max_length: Maximum line length in characters
        separator: Paragraph separator (preserved)
        language_model: spaCy language model to use

    Returns:
        Text with long lines split. Chapter titles are preserved.
    """
    lines = text.split("\n")
    result_lines: list[str] = []

    for line in lines:
        # Preserve chapter titles (short lines without typical sentence endings)
        is_likely_chapter_title = (
            len(line.strip()) < 100
            and line.strip()
            and not line.strip().endswith((".", "!", "?", '"', "'"))
        )

        if is_likely_chapter_title:
            result_lines.append(line)
            continue

        # Check if line is within limit
        if len(line) <= max_length:
            result_lines.append(line)
            continue

        # Determine if line starts with separator
        has_separator = line.startswith(separator) if separator else False
        content = line[len(separator) :] if has_separator else line

        # Split the long line using phrasplit (avoid calling ourselves)
        split_lines_list = _phrasplit_split_long_lines(
            content, max_length, language_model
        )
        # Defensive: if upstream ever returns a string, normalize to list
        if isinstance(split_lines_list, str):
            split_lines_list = [split_lines_list]
        # Add separator to first line if original had it
        for k, split_line in enumerate(split_lines_list):
            if k == 0 and has_separator:
                result_lines.append(separator + split_line)
            else:
                result_lines.append(split_line)

    return "\n".join(result_lines)


__all__ = [
    "collapse_paragraph",
    "format_paragraphs",
    "format_sentences",
    "format_clauses",
    "split_long_lines",
    "split_paragraphs",
]
