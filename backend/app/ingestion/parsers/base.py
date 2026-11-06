"""Base interface and context for language-specific parsers and text chunkers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.app.ingestion.models import CodeChunk


@dataclass(frozen=True)
class ChunkContext:
    """Repository and file metadata context provided to a parser during chunking."""

    repo_owner: str
    repo_name: str
    repo_url: str
    branch_or_commit: str | None
    file_path: str
    language: str


class BaseCodeParser(ABC):
    """Abstract base class for all syntax-aware parsers and text chunkers."""

    @abstractmethod
    def can_parse(self, language: str) -> bool:
        """Check if this parser can handle the requested language."""
        pass

    @abstractmethod
    def parse(self, content: str, context: ChunkContext) -> list[CodeChunk]:
        """Parse source content into a list of structured CodeChunks."""
        pass
