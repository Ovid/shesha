"""Tests for citation verification module."""

from shesha.rlm.verification import Citation, Quote, VerificationResult


class TestDataclasses:
    """Tests for verification dataclasses."""

    def test_citation_construction(self) -> None:
        """Citation stores doc_id and found status."""
        c = Citation(doc_id=5, found=True)
        assert c.doc_id == 5
        assert c.found is True

    def test_quote_construction(self) -> None:
        """Quote stores text, doc_id, and found status."""
        q = Quote(text="some quoted text here", doc_id=3, found=True)
        assert q.text == "some quoted text here"
        assert q.doc_id == 3
        assert q.found is True

    def test_verification_result_construction(self) -> None:
        """VerificationResult stores citations and quotes."""
        citations = [Citation(doc_id=1, found=True)]
        quotes = [Quote(text="example quote text", doc_id=1, found=True)]
        result = VerificationResult(citations=citations, quotes=quotes)
        assert len(result.citations) == 1
        assert len(result.quotes) == 1

    def test_verification_result_all_valid(self) -> None:
        """all_valid is True when all citations and quotes are found."""
        result = VerificationResult(
            citations=[Citation(doc_id=0, found=True), Citation(doc_id=1, found=True)],
            quotes=[Quote(text="some quote text", doc_id=0, found=True)],
        )
        assert result.all_valid is True

    def test_verification_result_not_all_valid_citation(self) -> None:
        """all_valid is False when a citation is not found."""
        result = VerificationResult(
            citations=[Citation(doc_id=999, found=False)],
            quotes=[],
        )
        assert result.all_valid is False

    def test_verification_result_not_all_valid_quote(self) -> None:
        """all_valid is False when a quote is not found."""
        result = VerificationResult(
            citations=[Citation(doc_id=0, found=True)],
            quotes=[Quote(text="fabricated text here", doc_id=0, found=False)],
        )
        assert result.all_valid is False

    def test_verification_result_empty_is_valid(self) -> None:
        """Empty verification result is valid."""
        result = VerificationResult(citations=[], quotes=[])
        assert result.all_valid is True
