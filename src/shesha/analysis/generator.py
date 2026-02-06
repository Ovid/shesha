"""Codebase analysis generator."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shesha import Shesha


class AnalysisGenerator:
    """Generates codebase analysis using RLM queries."""

    def __init__(self, shesha: "Shesha") -> None:
        """Initialize the generator.

        Args:
            shesha: Shesha instance for project access.
        """
        self._shesha = shesha
