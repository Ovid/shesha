"""Tests for the barsoom example."""

from examples.barsoom import BOOKS, format_stats, is_exit_command, parse_args
from shesha.rlm.trace import StepType, TokenUsage, Trace


class TestArgumentParsing:
    """Test CLI argument parsing."""

    def test_parse_args_default(self) -> None:
        """Default args have setup=False and verbose=False."""
        args = parse_args([])
        assert args.setup is False
        assert args.verbose is False

    def test_parse_args_setup_flag(self) -> None:
        """--setup flag sets setup=True."""
        args = parse_args(["--setup"])
        assert args.setup is True

    def test_parse_args_verbose_flag(self) -> None:
        """--verbose flag sets verbose=True."""
        args = parse_args(["--verbose"])
        assert args.verbose is True

    def test_parse_args_both_flags(self) -> None:
        """Both flags can be combined."""
        args = parse_args(["--setup", "--verbose"])
        assert args.setup is True
        assert args.verbose is True


class TestBooksMapping:
    """Test the BOOKS constant."""

    def test_books_has_seven_entries(self) -> None:
        """BOOKS maps 7 filenames to titles."""
        assert len(BOOKS) == 7

    def test_books_filenames_match_pattern(self) -> None:
        """All filenames follow barsoom-N.txt pattern."""
        for filename in BOOKS:
            assert filename.startswith("barsoom-")
            assert filename.endswith(".txt")

    def test_books_has_princess_of_mars(self) -> None:
        """First book is A Princess of Mars."""
        assert BOOKS["barsoom-1.txt"] == "A Princess of Mars"


class TestInputHandling:
    """Test user input handling."""

    def test_is_exit_command_quit(self) -> None:
        """'quit' is an exit command."""
        assert is_exit_command("quit") is True

    def test_is_exit_command_exit(self) -> None:
        """'exit' is an exit command."""
        assert is_exit_command("exit") is True

    def test_is_exit_command_case_insensitive(self) -> None:
        """Exit commands are case-insensitive."""
        assert is_exit_command("QUIT") is True
        assert is_exit_command("Exit") is True
        assert is_exit_command("QuIt") is True

    def test_is_exit_command_normal_input(self) -> None:
        """Normal questions are not exit commands."""
        assert is_exit_command("Who is Dejah Thoris?") is False
        assert is_exit_command("") is False
        assert is_exit_command("quitter") is False


class TestVerboseOutput:
    """Test verbose stats formatting."""

    def test_format_stats_includes_execution_time(self) -> None:
        """format_stats includes execution time in seconds."""
        token_usage = TokenUsage(prompt_tokens=1000, completion_tokens=500)
        trace = Trace()
        output = format_stats(execution_time=12.345, token_usage=token_usage, trace=trace)
        assert "12.35s" in output or "12.34s" in output

    def test_format_stats_includes_token_counts(self) -> None:
        """format_stats includes token breakdown."""
        token_usage = TokenUsage(prompt_tokens=3200, completion_tokens=1321)
        trace = Trace()
        output = format_stats(execution_time=1.0, token_usage=token_usage, trace=trace)
        assert "4521" in output  # total
        assert "3200" in output  # prompt
        assert "1321" in output  # completion

    def test_format_stats_includes_trace_steps(self) -> None:
        """format_stats includes trace step count."""
        token_usage = TokenUsage()
        trace = Trace()
        trace.add_step(StepType.CODE_GENERATED, "code", iteration=1)
        trace.add_step(StepType.CODE_OUTPUT, "output", iteration=1)
        trace.add_step(StepType.FINAL_ANSWER, "answer", iteration=1)
        output = format_stats(execution_time=1.0, token_usage=token_usage, trace=trace)
        assert "3" in output

    def test_format_stats_starts_with_separator(self) -> None:
        """format_stats starts with a separator line."""
        token_usage = TokenUsage()
        trace = Trace()
        output = format_stats(execution_time=1.0, token_usage=token_usage, trace=trace)
        assert output.startswith("---")
