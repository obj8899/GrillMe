"""Orchestrates repository ingestion: URL validation, fetching, filtering, and parsing."""

import tempfile
import time
from pathlib import Path

from backend.app.ingestion.file_filter import FileFilter
from backend.app.ingestion.github_client import (
    GitHubClient,
    extract_zipball_safely,
    parse_and_validate_github_url,
)
from backend.app.ingestion.models import (
    CodeChunk,
    EmptyRepoError,
    IngestionResponse,
    RepoMetadata,
)
from backend.app.ingestion.parsers import ChunkContext, ParserRegistry


class IngestionPipeline:
    """Coordinates fetching, filtering, and parsing of public GitHub repositories."""

    def __init__(
        self,
        github_client: GitHubClient | None = None,
        file_filter: FileFilter | None = None,
        parser_registry: ParserRegistry | None = None,
    ) -> None:
        self.github_client = github_client or GitHubClient()
        self.file_filter = file_filter or FileFilter()
        self.parser_registry = parser_registry or ParserRegistry()

    def ingest_from_archive(
        self,
        metadata: RepoMetadata,
        zip_bytes: bytes,
    ) -> tuple[IngestionResponse, list[CodeChunk]]:
        """Ingest repository from raw zip bytes in a sandboxed temporary directory.

        Guarantees that temporary files are purged from disk upon exit.
        """
        start_time = time.perf_counter()
        warnings: list[str] = []
        all_chunks: list[CodeChunk] = []

        with tempfile.TemporaryDirectory(prefix="grillme_ingest_") as temp_dir_str:
            temp_dir = Path(temp_dir_str)

            # Safely extract archive with Zip Slip protection
            extracted_files = extract_zipball_safely(zip_bytes, temp_dir)
            files_discovered = len(extracted_files)
            files_selected = 0
            files_skipped = 0

            for rel_path, abs_path in extracted_files:
                decision = self.file_filter.evaluate_file(rel_path, abs_path)
                if not decision.selected:
                    files_skipped += 1
                    continue

                files_selected += 1
                language = decision.language or "text"

                try:
                    content = abs_path.read_text(encoding="utf-8", errors="replace")
                except Exception as exc:
                    warnings.append(f"Failed to read '{rel_path}': {exc}")
                    files_skipped += 1
                    files_selected -= 1
                    continue

                context = ChunkContext(
                    repo_owner=metadata.owner,
                    repo_name=metadata.name,
                    repo_url=metadata.url,
                    branch_or_commit=metadata.default_branch,
                    file_path=rel_path,
                    language=language,
                )

                parser = self.parser_registry.get_parser(language)
                try:
                    chunks = parser.parse(content, context)
                    all_chunks.extend(chunks)
                except Exception as exc:
                    warnings.append(f"Error parsing '{rel_path}': {exc}")

            if files_selected == 0:
                raise EmptyRepoError(
                    f"Repository '{metadata.full_name}' contains no eligible source code "
                    "or documentation files."
                )

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status = "success" if not warnings else "partial_success"

            response = IngestionResponse(
                status=status,
                repository=metadata,
                files_discovered=files_discovered,
                files_selected=files_selected,
                files_skipped=files_skipped,
                chunks_produced=len(all_chunks),
                warnings=warnings,
                duration_ms=duration_ms,
            )

            return response, all_chunks

    async def ingest_url(self, repo_url: str) -> tuple[IngestionResponse, list[CodeChunk]]:
        """Complete ingestion workflow: validate URL, query GitHub API, fetch archive, and parse."""
        owner, repo = parse_and_validate_github_url(repo_url)
        metadata = await self.github_client.get_repo_metadata(owner, repo)
        zip_bytes = await self.github_client.download_repo_zipball(
            owner, repo, metadata.default_branch
        )
        return self.ingest_from_archive(metadata, zip_bytes)
