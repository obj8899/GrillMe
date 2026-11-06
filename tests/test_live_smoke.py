"""Opt-in live GitHub integration smoke test requiring active internet access.

Run manually via:
    pytest -m live
"""

import pytest
from fastapi.testclient import TestClient


@pytest.mark.live
def test_live_github_ingest_smoke(client: TestClient) -> None:
    """Smoke test ingesting a real, tiny public GitHub repository (octocat/Hello-World)."""
    response = client.post(
        "/api/ingest",
        json={"repo_url": "https://github.com/octocat/Hello-World"},
    )
    # If GitHub rate limit is reached on unauthenticated IP, status is 429
    assert response.status_code in (200, 429)

    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "success"
        assert data["repository"]["name"] == "Hello-World"
        assert data["files_selected"] >= 1
        assert data["chunks_produced"] >= 1
