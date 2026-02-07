"""Tests for semantic verification module."""

import pytest

from shesha.rlm.semantic_verification import (
    FindingVerification,
    SemanticVerificationReport,
)


class TestFindingVerification:
    """Tests for FindingVerification dataclass."""

    def test_construction(self) -> None:
        """FindingVerification stores all fields."""
        fv = FindingVerification(
            finding_id="F1",
            original_claim="The code uses async/await",
            confidence="high",
            reason="Found async keyword in source",
            evidence_classification="direct_quote",
        )
        assert fv.finding_id == "F1"
        assert fv.original_claim == "The code uses async/await"
        assert fv.confidence == "high"
        assert fv.reason == "Found async keyword in source"
        assert fv.evidence_classification == "direct_quote"
        assert fv.flags == []

    def test_flags_default_empty(self) -> None:
        """Flags defaults to empty list."""
        fv = FindingVerification(
            finding_id="F1",
            original_claim="claim",
            confidence="low",
            reason="reason",
            evidence_classification="unsupported",
        )
        assert fv.flags == []

    def test_flags_custom(self) -> None:
        """Flags can be set to a custom list."""
        fv = FindingVerification(
            finding_id="F1",
            original_claim="claim",
            confidence="medium",
            reason="reason",
            evidence_classification="inferred",
            flags=["speculative", "no_source"],
        )
        assert fv.flags == ["speculative", "no_source"]


class TestSemanticVerificationReport:
    """Tests for SemanticVerificationReport dataclass."""

    def test_construction(self) -> None:
        """SemanticVerificationReport stores findings and content_type."""
        findings = [
            FindingVerification(
                finding_id="F1",
                original_claim="claim1",
                confidence="high",
                reason="reason1",
                evidence_classification="direct_quote",
            ),
        ]
        report = SemanticVerificationReport(
            findings=findings,
            content_type="code",
        )
        assert len(report.findings) == 1
        assert report.content_type == "code"

    def test_high_confidence_filters_high_and_medium(self) -> None:
        """high_confidence returns findings with high or medium confidence."""
        findings = [
            FindingVerification(
                finding_id="F1",
                original_claim="claim1",
                confidence="high",
                reason="r1",
                evidence_classification="direct_quote",
            ),
            FindingVerification(
                finding_id="F2",
                original_claim="claim2",
                confidence="medium",
                reason="r2",
                evidence_classification="inferred",
            ),
            FindingVerification(
                finding_id="F3",
                original_claim="claim3",
                confidence="low",
                reason="r3",
                evidence_classification="unsupported",
            ),
        ]
        report = SemanticVerificationReport(findings=findings, content_type="general")
        high = report.high_confidence
        assert len(high) == 2
        assert high[0].finding_id == "F1"
        assert high[1].finding_id == "F2"

    def test_low_confidence_filters_only_low(self) -> None:
        """low_confidence returns only findings with low confidence."""
        findings = [
            FindingVerification(
                finding_id="F1",
                original_claim="claim1",
                confidence="high",
                reason="r1",
                evidence_classification="direct_quote",
            ),
            FindingVerification(
                finding_id="F2",
                original_claim="claim2",
                confidence="low",
                reason="r2",
                evidence_classification="unsupported",
            ),
            FindingVerification(
                finding_id="F3",
                original_claim="claim3",
                confidence="medium",
                reason="r3",
                evidence_classification="inferred",
            ),
        ]
        report = SemanticVerificationReport(findings=findings, content_type="general")
        low = report.low_confidence
        assert len(low) == 1
        assert low[0].finding_id == "F2"

    def test_empty_report_returns_empty_lists(self) -> None:
        """Empty report returns empty lists for both properties."""
        report = SemanticVerificationReport(findings=[], content_type="general")
        assert report.high_confidence == []
        assert report.low_confidence == []
