"""Semantic verification of RLM findings against source documents."""

from dataclasses import dataclass, field


@dataclass
class FindingVerification:
    """Verification result for a single finding."""

    finding_id: str
    original_claim: str
    confidence: str
    reason: str
    evidence_classification: str
    flags: list[str] = field(default_factory=list)


@dataclass
class SemanticVerificationReport:
    """Report containing verified findings."""

    findings: list[FindingVerification]
    content_type: str

    @property
    def high_confidence(self) -> list[FindingVerification]:
        """Return findings where confidence is high or medium."""
        return [f for f in self.findings if f.confidence in ("high", "medium")]

    @property
    def low_confidence(self) -> list[FindingVerification]:
        """Return findings where confidence is low."""
        return [f for f in self.findings if f.confidence == "low"]
