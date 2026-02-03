"""Git repository ingester."""

from pathlib import Path


class RepoIngester:
    """Handles git repository cloning, updating, and file extraction."""

    def __init__(self, storage_path: Path | str) -> None:
        """Initialize with storage path for cloned repos."""
        self.storage_path = Path(storage_path)
        self.repos_dir = self.storage_path / "repos"
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    def is_local_path(self, url: str) -> bool:
        """Check if url is a local filesystem path."""
        return url.startswith("/") or url.startswith("~") or Path(url).exists()
