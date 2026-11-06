"""Unit tests for safe repository archive extraction and Zip Slip prevention."""

import io
import tempfile
import zipfile
from pathlib import Path

import pytest

from backend.app.ingestion.github_client import extract_zipball_safely
from backend.app.ingestion.models import EmptyRepoError, RepoLimitExceededError


def create_in_memory_zip(file_map: dict[str, bytes]) -> bytes:
    """Helper to build an in-memory zip archive."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, data in file_map.items():
            zf.writestr(filename, data)
    return buf.getvalue()


def test_safe_extraction_normal_archive() -> None:
    """Normal GitHub zipball prefix is stripped and files are safely extracted."""
    zip_bytes = create_in_memory_zip({
        "myorg-myrepo-a1b2c3d/README.md": b"# My Repo",
        "myorg-myrepo-a1b2c3d/src/main.py": b"print('hello')",
    })

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        extracted = extract_zipball_safely(zip_bytes, tmp_dir)

        assert len(extracted) == 2
        rel_paths = [r for r, _ in extracted]
        assert "README.md" in rel_paths
        assert "src/main.py" in rel_paths

        # Verify on-disk file content
        readme_path = next(p for r, p in extracted if r == "README.md")
        assert readme_path.read_text(encoding="utf-8") == "# My Repo"


def test_zip_slip_path_traversal_is_neutralized() -> None:
    """Path traversal attacks attempting to escape the sandbox directory are skipped."""
    zip_bytes = create_in_memory_zip({
        "myorg-myrepo-a1b2c3d/safe.py": b"# Safe",
        "myorg-myrepo-a1b2c3d/../../evil.py": b"# Malicious",
        "../outside.py": b"# Malicious 2",
    })

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        extracted = extract_zipball_safely(zip_bytes, tmp_dir)

        # Only the safe file should be extracted
        rel_paths = [r for r, _ in extracted]
        assert "safe.py" in rel_paths
        assert not any("evil.py" in r or "outside.py" in r for r in rel_paths)

        # Verify no files were created outside tmp_dir
        parent_dir = tmp_dir.parent
        assert not (parent_dir / "evil.py").exists()
        assert not (parent_dir / "outside.py").exists()


def test_file_count_limit_exceeded() -> None:
    """When an archive exceeds max_file_count, RepoLimitExceededError is raised."""
    file_map = {f"prefix/file_{i}.txt": b"data" for i in range(10)}
    zip_bytes = create_in_memory_zip(file_map)

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        with pytest.raises(RepoLimitExceededError, match="file count exceeds limit"):
            extract_zipball_safely(zip_bytes, tmp_dir, max_file_count=5)


def test_total_unpacked_size_limit_exceeded() -> None:
    """When unpacked archive exceeds max_total_bytes, RepoLimitExceededError is raised."""
    zip_bytes = create_in_memory_zip({
        "prefix/large.bin": b"x" * 5000,
    })

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        with pytest.raises(RepoLimitExceededError, match="size exceeds limit"):
            extract_zipball_safely(zip_bytes, tmp_dir, max_total_bytes=1000)


def test_empty_archive_raises_error() -> None:
    """An archive with no extractable files raises EmptyRepoError."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as _:
        pass  # Completely empty zip
    empty_zip = buf.getvalue()

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        with pytest.raises(EmptyRepoError):
            extract_zipball_safely(empty_zip, tmp_dir)
