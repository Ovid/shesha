"""Tests for MultiRepoAnalyzer."""

import json
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


class TestMultiRepoAnalyzerAddRepo:
    """Tests for add_repo method."""

    def test_add_repo_creates_project(self):
        """add_repo creates a project via Shesha."""
        mock_shesha = MagicMock()
        mock_result = MagicMock()
        mock_result.project.project_id = "org-repo"
        mock_result.status = "created"
        mock_shesha.create_project_from_repo.return_value = mock_result

        analyzer = MultiRepoAnalyzer(mock_shesha)
        project_id = analyzer.add_repo("https://github.com/org/repo")

        assert project_id == "org-repo"
        assert "org-repo" in analyzer.repos
        mock_shesha.create_project_from_repo.assert_called_once_with("https://github.com/org/repo")

    def test_add_repo_reuses_existing(self):
        """add_repo reuses existing project if unchanged."""
        mock_shesha = MagicMock()
        mock_result = MagicMock()
        mock_result.project.project_id = "org-repo"
        mock_result.status = "unchanged"
        mock_shesha.create_project_from_repo.return_value = mock_result

        analyzer = MultiRepoAnalyzer(mock_shesha)
        project_id = analyzer.add_repo("https://github.com/org/repo")

        assert project_id == "org-repo"
        assert "org-repo" in analyzer.repos

    def test_add_repo_handles_updates(self):
        """add_repo applies updates if available."""
        mock_shesha = MagicMock()
        mock_result = MagicMock()
        mock_result.project.project_id = "org-repo"
        mock_result.status = "updates_available"
        mock_updated_result = MagicMock()
        mock_updated_result.project.project_id = "org-repo"
        mock_updated_result.status = "created"
        mock_result.apply_updates.return_value = mock_updated_result
        mock_shesha.create_project_from_repo.return_value = mock_result

        analyzer = MultiRepoAnalyzer(mock_shesha)
        project_id = analyzer.add_repo("https://github.com/org/repo")

        assert project_id == "org-repo"
        mock_result.apply_updates.assert_called_once()

    def test_add_repo_avoids_duplicates(self):
        """add_repo doesn't add the same repo twice."""
        mock_shesha = MagicMock()
        mock_result = MagicMock()
        mock_result.project.project_id = "org-repo"
        mock_result.status = "unchanged"
        mock_shesha.create_project_from_repo.return_value = mock_result

        analyzer = MultiRepoAnalyzer(mock_shesha)
        analyzer.add_repo("https://github.com/org/repo")
        analyzer.add_repo("https://github.com/org/repo")

        assert analyzer.repos.count("org-repo") == 1


class TestMultiRepoAnalyzerRecon:
    """Tests for Phase 1 recon."""

    def test_run_recon_queries_project(self):
        """Recon phase queries the project with recon prompt."""
        mock_shesha = MagicMock()
        mock_project = MagicMock()
        mock_project.project_id = "test-repo"
        mock_query_result = MagicMock()
        mock_query_result.answer = (
            json.dumps(
                {
                    "apis": ["GET /users"],
                    "models": ["User"],
                    "entry_points": ["main.py"],
                    "dependencies": ["postgres"],
                }
            )
            + "\n\nThis is a user service."
        )
        mock_project.query.return_value = mock_query_result
        mock_shesha.get_project.return_value = mock_project

        analyzer = MultiRepoAnalyzer(mock_shesha)
        analyzer._repos = ["test-repo"]

        summary = analyzer._run_recon("test-repo")

        assert summary.project_id == "test-repo"
        assert "GET /users" in summary.apis
        assert "User" in summary.models
        mock_project.query.assert_called_once()

    def test_run_recon_handles_malformed_json(self):
        """Recon gracefully handles non-JSON responses."""
        mock_shesha = MagicMock()
        mock_project = MagicMock()
        mock_project.project_id = "test-repo"
        mock_query_result = MagicMock()
        mock_query_result.answer = "This repo contains user management code."
        mock_project.query.return_value = mock_query_result
        mock_shesha.get_project.return_value = mock_project

        analyzer = MultiRepoAnalyzer(mock_shesha)
        analyzer._repos = ["test-repo"]

        summary = analyzer._run_recon("test-repo")

        assert summary.project_id == "test-repo"
        assert summary.raw_summary == "This repo contains user management code."
        # Lists should be empty when JSON parsing fails
        assert summary.apis == []


class TestMultiRepoAnalyzerImpact:
    """Tests for Phase 2 impact analysis."""

    def test_run_impact_queries_with_prd_and_summary(self):
        """Impact phase queries with PRD and repo summary."""
        mock_shesha = MagicMock()
        mock_project = MagicMock()
        mock_project.project_id = "test-repo"
        mock_query_result = MagicMock()
        mock_query_result.answer = json.dumps({
            "affected": True,
            "changes": ["Add new endpoint"],
            "new_interfaces": ["GET /new"],
            "modified_interfaces": ["POST /old"],
            "discovered_dependencies": ["other-service"],
        }) + "\n\nNeeds changes for OAuth."
        mock_project.query.return_value = mock_query_result
        mock_shesha.get_project.return_value = mock_project

        analyzer = MultiRepoAnalyzer(mock_shesha)

        summary = RepoSummary(
            project_id="test-repo",
            apis=["GET /users"],
            raw_summary="User service",
        )

        report = analyzer._run_impact("test-repo", "Add OAuth support", summary)

        assert report.project_id == "test-repo"
        assert report.affected is True
        assert "Add new endpoint" in report.changes
        assert "other-service" in report.discovered_dependencies

    def test_run_impact_not_affected(self):
        """Impact correctly identifies unaffected repos."""
        mock_shesha = MagicMock()
        mock_project = MagicMock()
        mock_project.project_id = "test-repo"
        mock_query_result = MagicMock()
        mock_query_result.answer = json.dumps({
            "affected": False,
            "changes": [],
            "new_interfaces": [],
            "modified_interfaces": [],
            "discovered_dependencies": [],
        }) + "\n\nNo changes needed."
        mock_project.query.return_value = mock_query_result
        mock_shesha.get_project.return_value = mock_project

        analyzer = MultiRepoAnalyzer(mock_shesha)

        summary = RepoSummary(project_id="test-repo", raw_summary="Logging service")

        report = analyzer._run_impact("test-repo", "Add OAuth support", summary)

        assert report.affected is False
        assert report.changes == []
