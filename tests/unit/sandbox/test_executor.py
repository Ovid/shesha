"""Tests for sandbox executor."""

from unittest.mock import MagicMock, patch

from shesha.sandbox.executor import ContainerExecutor, ExecutionResult


class TestContainerExecutor:
    """Tests for ContainerExecutor."""

    def test_execution_result_dataclass(self):
        """ExecutionResult stores execution output."""
        result = ExecutionResult(
            status="ok",
            stdout="Hello",
            stderr="",
            return_value=None,
            error=None,
            final_answer=None,
        )
        assert result.status == "ok"
        assert result.stdout == "Hello"

    @patch("shesha.sandbox.executor.docker")
    def test_executor_creates_container(self, mock_docker: MagicMock):
        """Executor creates a Docker container."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        executor = ContainerExecutor(image="shesha-sandbox")
        executor.start()

        mock_client.containers.run.assert_called_once()
        assert executor._container is not None

    @patch("shesha.sandbox.executor.docker")
    def test_executor_stops_container(self, mock_docker: MagicMock):
        """Executor stops and removes container on stop()."""
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        executor = ContainerExecutor(image="shesha-sandbox")
        executor.start()
        executor.stop()

        mock_container.stop.assert_called_once()
        mock_container.remove.assert_called_once()
