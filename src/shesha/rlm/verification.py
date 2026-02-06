"""Post-FINAL citation verification for RLM answers."""

from dataclasses import dataclass


@dataclass
class Citation:
    """A document citation found in an answer."""

    doc_id: int
    found: bool


@dataclass
class Quote:
    """A quoted string found in an answer."""

    text: str
    doc_id: int
    found: bool


@dataclass
class VerificationResult:
    """Result of citation verification."""

    citations: list[Citation]
    quotes: list[Quote]

    @property
    def all_valid(self) -> bool:
        """True when all citations and quotes were found."""
        return all(c.found for c in self.citations) and all(q.found for q in self.quotes)
