"""Abstract base class for processing pipelines."""

from abc import ABC, abstractmethod


class Pipeline(ABC):
    """Base class for all kb-tool processing pipelines."""

    @abstractmethod
    def process(self, input_data: str, config: dict | None = None) -> str:
        """Process input and return Markdown string.

        Args:
            input_data: Input URL, file path, or raw text
            config: Optional configuration dict

        Returns:
            Processed content as Markdown string
        """
        pass
