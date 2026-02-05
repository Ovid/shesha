"""Tests for MultiRepoAnalyzer."""

from unittest.mock import MagicMock

from shesha.experimental.multi_repo import MultiRepoAnalyzer
from shesha.experimental.multi_repo.models import ImpactReport, RepoSummary


class TestMultiRepoAnalyzerInit:
    """Tests for analyzer initialization."""

    def test_init_with_shesha_instance(self):
        """Analyzer initializes with a Shesha instance."""
        mock_shesha = MagicMock()
        analyzer = MultiRepoAnalyzer(mock_shesha)

        assert analyzer._shesha is mock_shesha
        assert analyzer._repos == []
        assert analyzer._summaries == {}
        assert analyzer._impacts == {}

    def test_init_with_custom_config(self):
        """Analyzer accepts custom configuration."""
        mock_shesha = MagicMock()
        analyzer = MultiRepoAnalyzer(
            mock_shesha,
            max_discovery_rounds=3,
            max_revision_rounds=4,
            phase_timeout_seconds=600,
            total_timeout_seconds=3600,
        )

        assert analyzer._max_discovery_rounds == 3
        assert analyzer._max_revision_rounds == 4
        assert analyzer._phase_timeout_seconds == 600
        assert analyzer._total_timeout_seconds == 3600

    def test_init_default_config(self):
        """Analyzer has sensible defaults."""
        mock_shesha = MagicMock()
        analyzer = MultiRepoAnalyzer(mock_shesha)

        assert analyzer._max_discovery_rounds == 2
        assert analyzer._max_revision_rounds == 2
        assert analyzer._phase_timeout_seconds == 300
        assert analyzer._total_timeout_seconds == 1800


class TestMultiRepoAnalyzerProperties:
    """Tests for analyzer properties."""

    def test_repos_property(self):
        """repos property returns list of project_ids."""
        mock_shesha = MagicMock()
        analyzer = MultiRepoAnalyzer(mock_shesha)
        analyzer._repos = ["repo-a", "repo-b"]

        assert analyzer.repos == ["repo-a", "repo-b"]

    def test_summaries_property(self):
        """summaries property returns dict of RepoSummary."""
        mock_shesha = MagicMock()
        analyzer = MultiRepoAnalyzer(mock_shesha)

        summary = RepoSummary(project_id="test", raw_summary="text")
        analyzer._summaries = {"test": summary}

        assert analyzer.summaries == {"test": summary}

    def test_impacts_property(self):
        """impacts property returns dict of ImpactReport."""
        mock_shesha = MagicMock()
        analyzer = MultiRepoAnalyzer(mock_shesha)

        report = ImpactReport(project_id="test", affected=True, raw_analysis="text")
        analyzer._impacts = {"test": report}

        assert analyzer.impacts == {"test": report}
