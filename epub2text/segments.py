"""Structured text segmentation."""

from __future__ import annotations

import re

from .structured import EntityRun, SourceRange, TextBlock, TextRun, TextSegment


def _split_offsets(text: str, mode: str) -> list[tuple[str, int, int]]:
    if not text:
        return []
    try:
        from phrasplit import split_with_offsets
    except ImportError:
        if mode == "paragraph":
            pattern = re.compile(r"[^\n]+(?:\n(?!\n)[^\n]+)*")
        else:
            pattern = re.compile(r"[^.!?]+[.!?]?\s*", re.S)
        result = []
        for m in pattern.finditer(text):
            value = m.group(0)
            if not value:
                continue
            trimmed = value.rstrip()
            result.append((trimmed, m.start(), m.start() + len(trimmed)))
        return result

    # Structured extraction should be deterministic and must not depend on an
    # ambient spaCy environment. An installed-but-incomplete spaCy package
    # without the language model would otherwise make segmentation fail.
    phrasplit_segments = split_with_offsets(text, mode=mode, use_spacy=False)
    result: list[tuple[str, int, int]] = []
    for seg in phrasplit_segments:
        start = getattr(seg, "char_start", getattr(seg, "start", None))
        end = getattr(seg, "char_end", getattr(seg, "end", None))
        if start is None or end is None:
            raise TypeError(
                "Unsupported phrasplit segment object: expected char_start/char_end"
            )
        result.append((seg.text, start, end))
    return result


def _ranges_for_segment(
    block: TextBlock, start: int, end: int
) -> tuple[SourceRange, ...]:
    ranges: list[SourceRange] = []
    for run in block.runs:
        if not isinstance(run, TextRun | EntityRun):
            continue
        run_start = run.block_text_start
        run_end = run.block_text_end
        overlap_start = max(start, run_start)
        overlap_end = min(end, run_end)
        if overlap_start >= overlap_end:
            continue
        source_start = run.source_char_start + (overlap_start - run_start)
        source_end = run.source_char_start + (overlap_end - run_start)
        ranges.append(
            SourceRange(
                block.document_id,
                source_start,
                source_end,
                getattr(run, "source_byte_start", None),
                getattr(run, "source_byte_end", None),
            )
        )
    return tuple(ranges)


def extract_segments(
    blocks: list[TextBlock], mode: str = "sentence"
) -> list[TextSegment]:
    segments: list[TextSegment] = []
    for block in blocks:
        for index, (text, start, end) in enumerate(_split_offsets(block.text, mode)):
            segments.append(
                TextSegment(
                    f"seg:{block.id}:{mode}:{index}:{start}:{end}",
                    block.id,
                    mode,
                    index,
                    text,
                    start,
                    end,
                    _ranges_for_segment(block, start, end),
                    block.chapter_id,
                    block.page_number,
                    [],
                )
            )
    return segments
