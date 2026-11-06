"""GitHub repository interaction: URL validation, metadata retrieval, and safe archive fetching."""

import io
import re
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import httpx

from backend.app.core.config import settings
from backend.app.ingestion.models import (
    EmptyRepoError,
    IngestionError,
    InvalidRepoUrlError,
    RepoAccessError,
    RepoLimitExceededError,
    RepoMetadata,
    RepoNotFoundError,
)

# Regex matching valid GitHub owner and repo names
GITHUB_IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\.]+$")


def parse_and_validate_github_url(url: str) -> tuple[str, str]:
    """Validate a public GitHub repository URL and extract (owner, repo).

    Supported formats:
        - https://github.com/owner/repo
        - http://github.com/owner/repo/
        - https://github.com/owner/repo.git

    Raises:
        InvalidRepoUrlError: If the URL is invalid, points to an unsupported host,
                             or contains malformed path components.
    """
    if not url or not isinstance(url, str):
        raise InvalidRepoUrlError("Repository URL must be a non-empty string.")

    cleaned_url = url.strip()
    try:
        parsed = urlparse(cleaned_url)
    except Exception as exc:
        raise InvalidRepoUrlError(f"Malformed URL: {exc}") from exc

    if not parsed.scheme or parsed.scheme.lower() not in ("http", "https"):
        raise InvalidRepoUrlError("URL scheme must be HTTP or HTTPS.")

    netloc = parsed.netloc.lower()
    # Normalize potential port or www
    if netloc.startswith("www."):
        netloc = netloc[4:]
    if ":" in netloc:
        netloc = netloc.split(":")[0]

    if netloc != "github.com":
        raise InvalidRepoUrlError(
            f"Unsupported host '{parsed.netloc}'. "
            "GrillMe currently supports public GitHub repositories only."
        )

    # Clean path: strip leading/trailing slashes
    path = parsed.path.strip("/")
    if not path:
        raise InvalidRepoUrlError("URL must contain repository owner and name.")

    parts = path.split("/")
    if len(parts) != 2:
        raise InvalidRepoUrlError(
            f"Expected URL path format '/owner/repo', but got '/{path}'."
        )

    owner, repo = parts[0].strip(), parts[1].strip()

    # Strip .git suffix if present
    if repo.endswith(".git"):
        repo = repo[:-4]

    if not owner or not repo:
        raise InvalidRepoUrlError("Both repository owner and name must be non-empty.")

    if not GITHUB_IDENTIFIER_PATTERN.match(owner) or not GITHUB_IDENTIFIER_PATTERN.match(repo):
        raise InvalidRepoUrlError(
            f"Invalid characters in owner '{owner}' or repo '{repo}'."
        )

    if owner in (".", "..") or repo in (".", ".."):
        raise InvalidRepoUrlError("Invalid path traversal sequence in repository identifier.")

    return owner, repo


class GitHubClient:
    """Client for querying GitHub API and downloading repository archives."""

    def __init__(
        self,
        api_base: str = settings.github_api_base,
        token: str | None = settings.github_token,
        timeout: float = 30.0,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.token = token
        self.timeout = timeout

    def _get_headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "GrillMe-Ingestion/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def get_repo_metadata(self, owner: str, repo: str) -> RepoMetadata:
        """Fetch repository metadata and default branch from GitHub API."""
        url = f"{self.api_base}/repos/{owner}/{repo}"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, headers=self._get_headers())
            except httpx.RequestError as exc:
                raise RepoAccessError(f"Network error contacting GitHub API: {exc}") from exc

        if response.status_code == 404:
            raise RepoNotFoundError(
                f"Repository '{owner}/{repo}' not found on GitHub (or is private)."
            )
        elif response.status_code == 403:
            # Check for rate limit
            rate_limit_remaining = response.headers.get("x-ratelimit-remaining")
            if rate_limit_remaining == "0":
                raise RepoAccessError(
                    "GitHub API rate limit exceeded. "
                    "Please configure GITHUB_TOKEN or try again later.",
                    status_code=429,
                )
            raise RepoAccessError(
                f"Access forbidden to repository '{owner}/{repo}': {response.text}",
                status_code=403,
            )
        elif response.status_code != 200:
            raise RepoAccessError(
                f"GitHub API returned unexpected status {response.status_code}: {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        default_branch = data.get("default_branch") or "main"
        is_empty = data.get("size", 1) == 0

        if is_empty:
            raise EmptyRepoError(f"Repository '{owner}/{repo}' is empty.")

        return RepoMetadata(
            owner=data.get("owner", {}).get("login", owner),
            name=data.get("name", repo),
            full_name=data.get("full_name", f"{owner}/{repo}"),
            url=data.get("html_url", f"https://github.com/{owner}/{repo}"),
            default_branch=default_branch,
            description=data.get("description"),
            stars=data.get("stargazers_count", 0),
        )

    async def download_repo_zipball(
        self, owner: str, repo: str, ref: str
    ) -> bytes:
        """Streamingly download repository zipball while enforcing size limits."""
        url = f"{self.api_base}/repos/{owner}/{repo}/zipball/{ref}"

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            try:
                async with client.stream("GET", url, headers=self._get_headers()) as response:
                    if response.status_code == 404:
                        raise RepoNotFoundError(
                            f"Archive for repository '{owner}/{repo}' at ref '{ref}' not found."
                        )
                    elif response.status_code == 403:
                        raise RepoAccessError(
                            "GitHub rate limit or access denied while downloading archive."
                        )
                    elif response.status_code != 200:
                        raise RepoAccessError(
                            "Failed to download repository archive "
                            f"(status {response.status_code})."
                        )

                    content_chunks: list[bytes] = []
                    total_bytes = 0

                    async for chunk in response.aiter_bytes():
                        total_bytes += len(chunk)
                        if total_bytes > settings.max_repo_size_bytes:
                            raise RepoLimitExceededError(
                                f"Repository archive size exceeds limit of "
                                f"{settings.max_repo_size_bytes} bytes."
                            )
                        content_chunks.append(chunk)

                    return b"".join(content_chunks)
            except httpx.RequestError as exc:
                raise RepoAccessError(
                    f"Network error downloading repository archive: {exc}"
                ) from exc


def extract_zipball_safely(
    zip_bytes: bytes,
    target_dir: Path,
    max_file_count: int = settings.max_file_count,
    max_total_bytes: int = settings.max_repo_size_bytes,
) -> list[tuple[str, Path]]:
    """Safely extract a repository zipball into target_dir.

    Features:
        - Prevents Zip Slip / path traversal attacks.
        - Strips the GitHub top-level archive prefix (e.g. 'owner-repo-sha/').
        - Enforces file count and total unpacked size limits.
        - Never executes repository code or runs any scripts.

    Returns:
        List of tuples: (relative_file_path_from_repo_root, absolute_path_on_disk).
    """
    extracted_files: list[tuple[str, Path]] = []
    total_unpacked_bytes = 0

    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            namelist = zf.namelist()
            if not namelist:
                raise EmptyRepoError("Repository archive is empty.")

            # Identify GitHub's top-level directory prefix if present
            # e.g. "owner-repo-7a1b2c3/"
            prefix = ""
            for name in namelist:
                if "/" in name:
                    candidate = name.split("/")[0]
                    if candidate and not candidate.startswith("."):
                        prefix = candidate + "/"
                        break

            file_count = 0
            resolved_target = target_dir.resolve()

            for member in zf.infolist():
                # Skip directory entries
                if member.is_dir() or member.filename.endswith("/"):
                    continue

                raw_filename = member.filename
                # Strip prefix to get clean relative path inside repo
                if prefix and raw_filename.startswith(prefix):
                    relative_path_str = raw_filename[len(prefix):]
                else:
                    relative_path_str = raw_filename

                if not relative_path_str:
                    continue

                # Path traversal defense: normalize and check
                # Disallow absolute paths, null bytes, or back-references
                if "\x00" in relative_path_str or relative_path_str.startswith(("/", "\\")):
                    continue

                norm_parts = Path(relative_path_str).parts
                if ".." in norm_parts:
                    continue

                dest_file_path = (resolved_target / relative_path_str).resolve()

                # Ensure destination resides strictly within resolved_target
                try:
                    dest_file_path.relative_to(resolved_target)
                except ValueError:
                    # Path is outside the sandbox target directory!
                    continue

                file_count += 1
                if file_count > max_file_count:
                    raise RepoLimitExceededError(
                        f"Repository file count exceeds limit of {max_file_count} files."
                    )

                total_unpacked_bytes += member.file_size
                if total_unpacked_bytes > max_total_bytes:
                    raise RepoLimitExceededError(
                        f"Unpacked repository size exceeds limit of {max_total_bytes} bytes."
                    )

                # Ensure parent directory exists
                dest_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file safely
                with zf.open(member) as source, open(dest_file_path, "wb") as target:
                    target.write(source.read())

                # Normalized forward-slash relative path
                normalized_rel_path = "/".join(norm_parts)
                extracted_files.append((normalized_rel_path, dest_file_path))

    except zipfile.BadZipFile as exc:
        raise IngestionError(f"Corrupt or invalid zip archive received: {exc}") from exc

    if not extracted_files:
        raise EmptyRepoError("No extractable files found in repository archive.")

    return extracted_files
