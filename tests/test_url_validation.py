"""Unit tests for GitHub URL validation and owner/repo extraction."""

import pytest

from backend.app.ingestion.github_client import parse_and_validate_github_url
from backend.app.ingestion.models import InvalidRepoUrlError


def test_valid_github_urls() -> None:
    """Test standard valid GitHub URLs."""
    res1 = parse_and_validate_github_url("https://github.com/torvalds/linux")
    assert res1 == ("torvalds", "linux")

    res2 = parse_and_validate_github_url("http://github.com/fastapi/fastapi")
    assert res2 == ("fastapi", "fastapi")

    res3 = parse_and_validate_github_url("https://github.com/my-org/my_repo.v2")
    assert res3 == ("my-org", "my_repo.v2")


def test_valid_github_url_variations() -> None:
    """Test valid URLs with trailing slashes, whitespace, .git suffix, and www prefix."""
    assert parse_and_validate_github_url("https://github.com/owner/repo/") == ("owner", "repo")
    assert parse_and_validate_github_url("https://github.com/owner/repo.git") == ("owner", "repo")
    assert parse_and_validate_github_url("https://github.com/owner/repo.git/") == ("owner", "repo")
    assert parse_and_validate_github_url("  https://github.com/owner/repo  ") == ("owner", "repo")
    assert parse_and_validate_github_url("https://www.github.com/owner/repo") == ("owner", "repo")


def test_unsupported_hosts() -> None:
    """Test rejection of non-GitHub hosts."""
    with pytest.raises(InvalidRepoUrlError, match="Unsupported host"):
        parse_and_validate_github_url("https://gitlab.com/owner/repo")

    with pytest.raises(InvalidRepoUrlError, match="Unsupported host"):
        parse_and_validate_github_url("https://bitbucket.org/owner/repo")

    with pytest.raises(InvalidRepoUrlError, match="Unsupported host"):
        parse_and_validate_github_url("https://example.com/owner/repo")


def test_invalid_url_schemes() -> None:
    """Test rejection of non-HTTP schemes or missing schemes."""
    with pytest.raises(InvalidRepoUrlError, match="URL scheme must be HTTP or HTTPS"):
        parse_and_validate_github_url("ftp://github.com/owner/repo")

    with pytest.raises(InvalidRepoUrlError, match="URL scheme must be HTTP or HTTPS"):
        parse_and_validate_github_url("git@github.com:owner/repo.git")

    with pytest.raises(InvalidRepoUrlError, match="URL scheme must be HTTP or HTTPS"):
        parse_and_validate_github_url("github.com/owner/repo")


def test_malformed_paths() -> None:
    """Test rejection of incomplete or overly deep URL paths."""
    # Missing repo
    with pytest.raises(InvalidRepoUrlError, match="Expected URL path format"):
        parse_and_validate_github_url("https://github.com/owner")

    # Missing owner and repo
    with pytest.raises(InvalidRepoUrlError, match="URL must contain repository owner and name"):
        parse_and_validate_github_url("https://github.com/")

    # Extra path segments (e.g. tree/main)
    with pytest.raises(InvalidRepoUrlError, match="Expected URL path format"):
        parse_and_validate_github_url("https://github.com/owner/repo/tree/main")


def test_invalid_characters_and_path_traversal() -> None:
    """Test rejection of path traversal attempts or invalid characters in names."""
    with pytest.raises(InvalidRepoUrlError, match="Invalid path traversal"):
        parse_and_validate_github_url("https://github.com/../repo")

    with pytest.raises(InvalidRepoUrlError, match="Invalid path traversal"):
        parse_and_validate_github_url("https://github.com/owner/..")

    with pytest.raises(InvalidRepoUrlError, match="Invalid characters"):
        parse_and_validate_github_url("https://github.com/owner$/repo")

    with pytest.raises(InvalidRepoUrlError, match="must be a non-empty string"):
        parse_and_validate_github_url("")
