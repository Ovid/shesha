"""Tests for analysis generator."""


class TestAnalysisGeneratorStructure:
    """Tests for AnalysisGenerator class structure."""

    def test_generator_can_be_imported(self):
        """AnalysisGenerator can be imported from shesha.analysis."""
        from shesha.analysis import AnalysisGenerator

        assert AnalysisGenerator is not None

    def test_generator_takes_shesha_instance(self):
        """AnalysisGenerator constructor takes a Shesha instance."""
        from unittest.mock import MagicMock

        from shesha.analysis import AnalysisGenerator

        mock_shesha = MagicMock()
        generator = AnalysisGenerator(mock_shesha)

        assert generator._shesha is mock_shesha
