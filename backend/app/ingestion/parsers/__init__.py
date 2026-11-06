"""Parser registry and exports for source code and documentation chunkers."""

from backend.app.ingestion.parsers.base import BaseCodeParser, ChunkContext
from backend.app.ingestion.parsers.fallback_text import FallbackTextChunker
from backend.app.ingestion.parsers.js_ts_parser import JavaScriptTypeScriptParser
from backend.app.ingestion.parsers.python_parser import PythonParser


class ParserRegistry:
    """Registry managing language parsers with fallback handling."""

    def __init__(self) -> None:
        self.fallback = FallbackTextChunker()
        self._parsers: list[BaseCodeParser] = [
            PythonParser(fallback_chunker=self.fallback),
            JavaScriptTypeScriptParser(fallback_chunker=self.fallback),
        ]

    def register(self, parser: BaseCodeParser) -> None:
        """Register an additional parser ahead of the fallback chunker."""
        self._parsers.insert(0, parser)

    def get_parser(self, language: str) -> BaseCodeParser:
        """Find the first matching parser for the language, or return fallback."""
        for parser in self._parsers:
            if parser.can_parse(language):
                return parser
        return self.fallback


__all__ = [
    "BaseCodeParser",
    "ChunkContext",
    "FallbackTextChunker",
    "JavaScriptTypeScriptParser",
    "ParserRegistry",
    "PythonParser",
]
