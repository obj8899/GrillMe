"""Data models and exception definitions for repository ingestion and parsing."""

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class IngestionError(Exception):
    """Base exception for all repository ingestion and parsing errors."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class InvalidRepoUrlError(IngestionError):
    """Raised when a provided repository URL is malformed or invalid."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


class RepoNotFoundError(IngestionError):
    """Raised when a repository does not exist or is inaccessible."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=404)


class RepoAccessError(IngestionError):
    """Raised when GitHub API requests fail (e.g. rate limit or network issue)."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message, status_code=status_code)


class EmptyRepoError(IngestionError):
    """Raised when an ingested repository has no files or content."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=422)


class RepoLimitExceededError(IngestionError):
    """Raised when repository size or file count exceeds safety limits."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=413)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class RepoMetadata(BaseModel):
    """Normalized metadata for an ingested GitHub repository."""

    owner: str = Field(..., description="Repository owner or organization name")
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository identifier, e.g. 'owner/repo'")
    url: str = Field(..., description="Canonical repository web URL")
    default_branch: str = Field(default="main", description="Default Git branch name")
    description: str | None = Field(default=None, description="Repository description if available")
    stars: int = Field(default=0, description="Star count")
    commit_sha: str | None = Field(default=None, description="Head commit SHA for this ingestion")


class CodeChunk(BaseModel):
    """A granular, structured chunk of code or documentation with source citations."""

    repo_owner: str = Field(..., description="Repository owner")
    repo_name: str = Field(..., description="Repository name")
    repo_url: str = Field(..., description="Repository URL")
    branch_or_commit: str | None = Field(None, description="Branch or commit SHA")
    file_path: str = Field(..., description="Relative file path from repository root")
    language: str = Field(..., description="Language identifier (e.g. 'python', 'typescript')")
    content: str = Field(..., description="Code or text content of this chunk")
    chunk_index: int = Field(..., description="Sequential index of the chunk")
    start_line: int | None = Field(None, description="1-based start line number in original file")
    end_line: int | None = Field(None, description="1-based end line number in original file")
    symbol_name: str | None = Field(
        None, description="Symbol name if parsed structurally (class/function name)"
    )
    chunk_type: str = Field(
        ...,
        description="Type of chunk (e.g. 'function', 'class', 'method', 'module', 'text_block')",
    )


class IngestionRequest(BaseModel):
    """Payload for initiating repository ingestion."""

    repo_url: str = Field(..., description="Public GitHub repository URL to ingest")


class IngestionResponse(BaseModel):
    """Summary response for an ingestion and code parsing run."""

    status: str = Field(
        ..., description="Overall ingestion outcome ('success', 'partial_success', 'failed')"
    )
    repository: RepoMetadata = Field(..., description="Metadata of the ingested repository")
    files_discovered: int = Field(..., description="Total files discovered in the archive")
    files_selected: int = Field(..., description="Files selected for parsing after filtering")
    files_skipped: int = Field(..., description="Files skipped due to filter or size limits")
    chunks_produced: int = Field(
        ..., description="Total structured chunks produced across all files"
    )
    warnings: list[str] = Field(default_factory=list, description="Warnings encountered during run")
    duration_ms: float | None = Field(
        None, description="Processing duration in milliseconds"
    )
