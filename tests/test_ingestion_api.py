"""Integration tests for the /api/ingest endpoint and pipeline error handling."""

import io
import zipfile
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.app.ingestion.models import (
    EmptyRepoError,
    RepoAccessError,
    RepoLimitExceededError,
    RepoMetadata,
    RepoNotFoundError,
)


def make_test_zip() -> bytes:
    """Create in-memory zip fixture containing Python, TypeScript, and Markdown files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "testorg-testrepo-abc1234/README.md",
            "# Sample Project\nA mock project for GrillMe testing.",
        )
        zf.writestr(
            "testorg-testrepo-abc1234/src/main.py",
            "def calculate(x: int) -> int:\n    return x + 1\n",
        )
        zf.writestr(
            "testorg-testrepo-abc1234/src/client.ts",
            "export class ApiClient {\n    async fetch(): Promise<void> {}\n}\n",
        )
        # Should be filtered out
        zf.writestr("testorg-testrepo-abc1234/node_modules/pkg/index.js", "console.log('skip');")
        zf.writestr("testorg-testrepo-abc1234/assets/logo.png", b"\x89PNG\r\n\x1a\n")
    return buf.getvalue()


def test_ingest_successful_flow(client: TestClient) -> None:
    """Verify successful ingestion using mocked GitHub API and controlled zip fixture."""
    mock_metadata = RepoMetadata(
        owner="testorg",
        name="testrepo",
        full_name="testorg/testrepo",
        url="https://github.com/testorg/testrepo",
        default_branch="main",
        description="A mock project",
        stars=42,
    )
    test_zip_bytes = make_test_zip()

    meta_target = "backend.app.ingestion.github_client.GitHubClient.get_repo_metadata"
    zip_target = "backend.app.ingestion.github_client.GitHubClient.download_repo_zipball"

    with (
        patch(meta_target, new_callable=AsyncMock) as mock_get_meta,
        patch(zip_target, new_callable=AsyncMock) as mock_download,
    ):
        mock_get_meta.return_value = mock_metadata
        mock_download.return_value = test_zip_bytes

        response = client.post(
            "/api/ingest",
            json={"repo_url": "https://github.com/testorg/testrepo"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert data["repository"]["owner"] == "testorg"
        assert data["repository"]["name"] == "testrepo"
        assert data["repository"]["stars"] == 42
        assert data["files_discovered"] == 5
        assert data["files_selected"] == 3  # README.md, main.py, client.ts
        assert data["files_skipped"] == 2   # node_modules and logo.png
        assert data["chunks_produced"] >= 3
        assert isinstance(data["duration_ms"], (int, float))
        assert data["duration_ms"] > 0


def test_ingest_invalid_url_returns_400(client: TestClient) -> None:
    """Invalid URL or non-GitHub host returns HTTP 400 Bad Request."""
    res_host = client.post("/api/ingest", json={"repo_url": "https://gitlab.com/owner/repo"})
    assert res_host.status_code == 400
    assert "Unsupported host" in res_host.json()["detail"]

    res_malformed = client.post("/api/ingest", json={"repo_url": "not-a-valid-url"})
    assert res_malformed.status_code == 400


def test_ingest_repo_not_found_returns_404(client: TestClient) -> None:
    """Non-existent or private repo returns HTTP 404 Not Found."""
    with patch(
        "backend.app.ingestion.github_client.GitHubClient.get_repo_metadata",
        new_callable=AsyncMock,
        side_effect=RepoNotFoundError("Repository 'ghost/missing' not found on GitHub."),
    ):
        response = client.post(
            "/api/ingest",
            json={"repo_url": "https://github.com/ghost/missing"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_ingest_empty_repo_returns_422(client: TestClient) -> None:
    """Empty repository returns HTTP 422 Unprocessable Entity."""
    with patch(
        "backend.app.ingestion.github_client.GitHubClient.get_repo_metadata",
        new_callable=AsyncMock,
        side_effect=EmptyRepoError("Repository 'empty/repo' is empty."),
    ):
        response = client.post(
            "/api/ingest",
            json={"repo_url": "https://github.com/empty/repo"},
        )
        assert response.status_code == 422
        assert "is empty" in response.json()["detail"].lower()


def test_ingest_repo_limit_exceeded_returns_413(client: TestClient) -> None:
    """Oversized repository returns HTTP 413 Payload Too Large."""
    with patch(
        "backend.app.ingestion.github_client.GitHubClient.get_repo_metadata",
        new_callable=AsyncMock,
        return_value=RepoMetadata(
            owner="huge",
            name="repo",
            full_name="huge/repo",
            url="https://github.com/huge/repo",
            default_branch="main",
        ),
    ), patch(
        "backend.app.ingestion.github_client.GitHubClient.download_repo_zipball",
        new_callable=AsyncMock,
        side_effect=RepoLimitExceededError(
            "Repository archive size exceeds limit of 52428800 bytes."
        ),
    ):
        response = client.post(
            "/api/ingest",
            json={"repo_url": "https://github.com/huge/repo"},
        )
        assert response.status_code == 413
        assert "exceeds limit" in response.json()["detail"].lower()


def test_ingest_rate_limit_or_access_error_returns_status(client: TestClient) -> None:
    """GitHub rate limit error returns HTTP 429."""
    with patch(
        "backend.app.ingestion.github_client.GitHubClient.get_repo_metadata",
        new_callable=AsyncMock,
        side_effect=RepoAccessError("GitHub API rate limit exceeded.", status_code=429),
    ):
        response = client.post(
            "/api/ingest",
            json={"repo_url": "https://github.com/owner/repo"},
        )
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"].lower()
