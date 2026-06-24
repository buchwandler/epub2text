"""Structured text segmentation."""

from __future__ import annotations

import re

from .structured import EntityRun, SourceRange, TextBlock, TextRun, TextSegment


def _split_offsets(text: str, mode: str) -> list[tuple[str, int, int]]:
    if not text:
        return []
    try:
        from phrasplit import split_with_offsets

        return [
            (seg.text, seg.start, seg.end)
            for seg in split_with_offsets(text, mode=mode)
        ]
    except Exception:
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
