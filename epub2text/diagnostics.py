"""Diagnostics for structured EPUB extraction."""

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Diagnostic:
    """A structured extraction diagnostic."""

    severity: Literal["info", "warning", "error"]
    code: str
    message: str
    document_href: str | None = None
    source_char_start: int | None = None
    source_char_end: int | None = None


class StrictExtractionError(ValueError):
    """Raised when strict structured extraction encounters diagnostics."""

    def __init__(self, diagnostics: list[Diagnostic]):
        self.diagnostics = diagnostics
        super().__init__("Structured extraction failed strict checks")
