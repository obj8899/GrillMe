"""Sliding-window text chunker for documentation and unsupported languages."""

from backend.app.core.config import settings
from backend.app.ingestion.models import CodeChunk
from backend.app.ingestion.parsers.base import BaseCodeParser, ChunkContext


class FallbackTextChunker(BaseCodeParser):
    """Deterministic sliding-window text chunker with line-boundary preservation."""

    def __init__(
        self,
        chunk_size_lines: int = settings.chunk_size_lines,
        chunk_overlap_lines: int = settings.chunk_overlap_lines,
    ) -> None:
        self.chunk_size_lines = max(5, chunk_size_lines)
        # Ensure overlap is strictly less than chunk size
        self.chunk_overlap_lines = max(0, min(chunk_overlap_lines, self.chunk_size_lines - 1))

    def can_parse(self, language: str) -> bool:
        """Fallback chunker accepts any language."""
        return True

    def parse(self, content: str, context: ChunkContext) -> list[CodeChunk]:
        """Split content into overlapping line-based text chunks."""
        if not content or not content.strip():
            return []

        lines = content.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return []

        # If file is within a single chunk window
        if total_lines <= self.chunk_size_lines:
            return [
                CodeChunk(
                    repo_owner=context.repo_owner,
                    repo_name=context.repo_name,
                    repo_url=context.repo_url,
                    branch_or_commit=context.branch_or_commit,
                    file_path=context.file_path,
                    language=context.language,
                    content=content,
                    chunk_index=0,
                    start_line=1,
                    end_line=total_lines,
                    symbol_name=None,
                    chunk_type="text_block",
                )
            ]

        chunks: list[CodeChunk] = []
        step = self.chunk_size_lines - self.chunk_overlap_lines
        chunk_idx = 0

        for start_idx in range(0, total_lines, step):
            end_idx = min(start_idx + self.chunk_size_lines, total_lines)
            chunk_lines = lines[start_idx:end_idx]
            chunk_content = "\n".join(chunk_lines).strip()

            if chunk_content:
                chunks.append(
                    CodeChunk(
                        repo_owner=context.repo_owner,
                        repo_name=context.repo_name,
                        repo_url=context.repo_url,
                        branch_or_commit=context.branch_or_commit,
                        file_path=context.file_path,
                        language=context.language,
                        content=chunk_content,
                        chunk_index=chunk_idx,
                        start_line=start_idx + 1,
                        end_line=end_idx,
                        symbol_name=None,
                        chunk_type="text_block",
                    )
                )
                chunk_idx += 1

            # Break if we have covered the last line
            if end_idx >= total_lines:
                break

        return chunks
