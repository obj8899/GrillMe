"""Unit tests for repository file selection and noise exclusion filtering."""

import tempfile
from pathlib import Path

from backend.app.ingestion.file_filter import FileFilter


def test_source_and_docs_are_selected() -> None:
    """Verify source code and documentation paths are selected with correct language."""
    f = FileFilter()

    # Python
    d1 = f.evaluate_path("src/grillme/main.py")
    assert d1.selected is True
    assert d1.language == "python"

    # TypeScript
    d2 = f.evaluate_path("frontend/src/App.tsx")
    assert d2.selected is True
    assert d2.language == "typescript"

    # JavaScript
    d3 = f.evaluate_path("scripts/bundle.js")
    assert d3.selected is True
    assert d3.language == "javascript"

    # Markdown
    d4 = f.evaluate_path("README.md")
    assert d4.selected is True
    assert d4.language == "markdown"

    # General config / unsupported code
    d5 = f.evaluate_path("config.toml")
    assert d5.selected is True
    assert d5.language == "toml"


def test_excluded_directories_are_rejected() -> None:
    """Verify standard vendor, build, and cache directories are rejected."""
    f = FileFilter()

    assert f.evaluate_path("node_modules/react/index.js").selected is False
    assert f.evaluate_path(".git/HEAD").selected is False
    assert f.evaluate_path(".venv/lib/python3.11/site.py").selected is False
    assert f.evaluate_path("dist/bundle.js").selected is False
    assert f.evaluate_path("build/output.js").selected is False
    assert f.evaluate_path("__pycache__/main.cpython-311.pyc").selected is False
    assert f.evaluate_path(".pytest_cache/v/cache/stepwise").selected is False
    assert f.evaluate_path("htmlcov/index.html").selected is False


def test_binary_extensions_are_rejected() -> None:
    """Verify binary extensions are detected and excluded."""
    f = FileFilter()

    assert f.evaluate_path("assets/logo.png").selected is False
    assert f.evaluate_path("docs/manual.pdf").selected is False
    assert f.evaluate_path("archive.zip").selected is False
    assert f.evaluate_path("lib/native.so").selected is False
    assert f.evaluate_path("bin/app.exe").selected is False
    assert f.evaluate_path("fonts/inter.woff2").selected is False


def test_lockfiles_and_minified_assets_are_rejected() -> None:
    """Verify package manager lockfiles and minified code are excluded."""
    f = FileFilter()

    assert f.evaluate_path("package-lock.json").selected is False
    assert f.evaluate_path("yarn.lock").selected is False
    assert f.evaluate_path("poetry.lock").selected is False
    assert f.evaluate_path("vendor/jquery.min.js").selected is False
    assert f.evaluate_path("styles/bundle.min.css").selected is False


def test_file_size_and_binary_content_evaluation() -> None:
    """Verify on-disk file checks: empty file, oversized file, binary null bytes."""
    f = FileFilter(max_file_size_bytes=100)

    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        # 1. Valid file
        valid_file = tmp_dir / "valid.py"
        valid_file.write_text("print('hello world')", encoding="utf-8")
        assert f.evaluate_file("valid.py", valid_file).selected is True

        # 2. Empty file
        empty_file = tmp_dir / "empty.py"
        empty_file.write_text("", encoding="utf-8")
        res_empty = f.evaluate_file("empty.py", empty_file)
        assert res_empty.selected is False
        assert "empty" in str(res_empty.reason).lower()

        # 3. Oversized file
        large_file = tmp_dir / "large.py"
        large_file.write_text("x" * 200, encoding="utf-8")
        res_large = f.evaluate_file("large.py", large_file)
        assert res_large.selected is False
        assert "exceeds limit" in str(res_large.reason).lower()

        # 4. Binary null bytes inside a .py extension
        fake_py = tmp_dir / "fake.py"
        fake_py.write_bytes(b"\x00\x01\x02\x03def foo(): pass")
        res_fake = f.evaluate_file("fake.py", fake_py)
        assert res_fake.selected is False
        assert "null bytes" in str(res_fake.reason).lower()
