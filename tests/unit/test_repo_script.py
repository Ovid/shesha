"""Tests for repo.py script."""


class TestParseArgs:
    """Tests for parse_args function."""

    def test_no_args(self) -> None:
        """No args should work (for picker mode)."""
        from examples.repo import parse_args

        args = parse_args([])
        assert args.repo is None
        assert not args.update
        assert not args.verbose

    def test_repo_positional(self) -> None:
        """Repo URL should be captured as positional arg."""
        from examples.repo import parse_args

        args = parse_args(["https://github.com/user/repo"])
        assert args.repo == "https://github.com/user/repo"

    def test_local_path(self) -> None:
        """Local path should be captured."""
        from examples.repo import parse_args

        args = parse_args(["/path/to/repo"])
        assert args.repo == "/path/to/repo"

    def test_update_flag(self) -> None:
        """--update flag should be captured."""
        from examples.repo import parse_args

        args = parse_args(["https://github.com/user/repo", "--update"])
        assert args.update

    def test_verbose_flag(self) -> None:
        """--verbose flag should be captured."""
        from examples.repo import parse_args

        args = parse_args(["https://github.com/user/repo", "--verbose"])
        assert args.verbose
