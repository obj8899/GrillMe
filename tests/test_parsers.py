"""Unit tests for Python, JavaScript/TypeScript, and Fallback text parsers."""

from backend.app.ingestion.parsers import (
    ChunkContext,
    FallbackTextChunker,
    JavaScriptTypeScriptParser,
    ParserRegistry,
    PythonParser,
)


def make_context(file_path: str, language: str) -> ChunkContext:
    return ChunkContext(
        repo_owner="test-owner",
        repo_name="test-repo",
        repo_url="https://github.com/test-owner/test-repo",
        branch_or_commit="main",
        file_path=file_path,
        language=language,
    )


# ---------------------------------------------------------------------------
# Fallback Text Chunker Tests
# ---------------------------------------------------------------------------


def test_fallback_empty_content() -> None:
    """Empty or whitespace content produces no chunks."""
    chunker = FallbackTextChunker()
    ctx = make_context("README.md", "markdown")
    assert chunker.parse("", ctx) == []
    assert chunker.parse("   \n\n  ", ctx) == []


def test_fallback_small_content() -> None:
    """Content smaller than chunk_size produces exactly one chunk with accurate lines."""
    chunker = FallbackTextChunker(chunk_size_lines=10, chunk_overlap_lines=2)
    ctx = make_context("README.md", "markdown")
    content = "# Title\n\nThis is a small documentation file."
    chunks = chunker.parse(content, ctx)

    assert len(chunks) == 1
    c = chunks[0]
    assert c.file_path == "README.md"
    assert c.language == "markdown"
    assert c.chunk_type == "text_block"
    assert c.start_line == 1
    assert c.end_line == 3
    assert c.symbol_name is None
    assert c.chunk_index == 0


def test_fallback_sliding_window_overlap() -> None:
    """Multi-line content produces overlapping chunks without empty gaps."""
    chunker = FallbackTextChunker(chunk_size_lines=5, chunk_overlap_lines=2)
    ctx = make_context("notes.txt", "text")
    lines = [f"Line {i}" for i in range(1, 13)]
    content = "\n".join(lines)

    chunks = chunker.parse(content, ctx)
    assert len(chunks) >= 3

    # Check sequential chunk indexing
    for idx, c in enumerate(chunks):
        assert c.chunk_index == idx
        assert c.start_line is not None
        assert c.end_line is not None
        assert c.start_line <= c.end_line

    # First chunk: lines 1..5
    assert chunks[0].start_line == 1
    assert chunks[0].end_line == 5

    # Second chunk: lines 4..8 (overlap of 2: step is 3)
    assert chunks[1].start_line == 4
    assert chunks[1].end_line == 8


# ---------------------------------------------------------------------------
# Python Parser Tests
# ---------------------------------------------------------------------------


def test_python_function_and_class_extraction() -> None:
    """Python parser extracts top-level functions, classes, and decorators with line numbers."""
    parser = PythonParser()
    ctx = make_context("app/service.py", "python")

    code = '''import os

@decorator_one
def compute_value(x: int) -> int:
    """Docstring for compute."""
    return x * 2

class Calculator:
    """Calculator helper class."""
    def add(self, a, b):
        return a + b
'''
    chunks = parser.parse(code, ctx)
    assert len(chunks) >= 2

    # Verify compute_value function
    func_chunk = next(c for c in chunks if c.symbol_name == "compute_value")
    assert func_chunk.chunk_type == "function"
    assert func_chunk.start_line == 3  # Decorator line
    assert "def compute_value" in func_chunk.content

    # Verify Calculator class
    class_chunk = next(c for c in chunks if c.symbol_name == "Calculator")
    assert class_chunk.chunk_type == "class"
    assert "class Calculator" in class_chunk.content


def test_python_syntax_error_fallback() -> None:
    """On Python syntax errors, parser falls back to text chunker rather than raising."""
    parser = PythonParser()
    ctx = make_context("broken.py", "python")
    broken_code = "def invalid_syntax(:::\n    broken line"
    chunks = parser.parse(broken_code, ctx)

    assert len(chunks) == 1
    assert chunks[0].chunk_type == "text_block"


# ---------------------------------------------------------------------------
# JavaScript and TypeScript Parser Tests
# ---------------------------------------------------------------------------


def test_javascript_structural_extraction() -> None:
    """JS parser extracts function declarations, classes, and arrow functions."""
    parser = JavaScriptTypeScriptParser()
    ctx = make_context("utils.js", "javascript")

    code = '''import lodash from 'lodash';

export class UserService {
    getUser(id) {
        return { id };
    }
}

export function formatUserName(user) {
    return user.name;
}

const calculateDiscount = (price, rate) => {
    return price * rate;
};
'''
    chunks = parser.parse(code, ctx)
    assert len(chunks) >= 3

    symbols = [c.symbol_name for c in chunks if c.symbol_name]
    assert "UserService" in symbols
    assert "formatUserName" in symbols
    assert "calculateDiscount" in symbols


def test_typescript_tsx_extraction() -> None:
    """TypeScript TSX parser handles typed components and interfaces."""
    parser = JavaScriptTypeScriptParser()
    ctx = make_context("components/Button.tsx", "typescript")

    code = '''import React from 'react';

interface ButtonProps {
    label: string;
    onClick: () => void;
}

export const Button: React.FC<ButtonProps> = ({ label, onClick }) => {
    return <button onClick={onClick}>{label}</button>;
};

export class ModalComponent extends React.Component {
    render() {
        return <div>Modal</div>;
    }
}
'''
    chunks = parser.parse(code, ctx)
    assert len(chunks) >= 2

    symbols = [c.symbol_name for c in chunks if c.symbol_name]
    assert "Button" in symbols
    assert "ModalComponent" in symbols


def test_parser_registry_selection() -> None:
    """ParserRegistry selects appropriate parser based on language tag."""
    registry = ParserRegistry()

    py_parser = registry.get_parser("python")
    assert isinstance(py_parser, PythonParser)

    js_parser = registry.get_parser("javascript")
    assert isinstance(js_parser, JavaScriptTypeScriptParser)

    ts_parser = registry.get_parser("typescript")
    assert isinstance(ts_parser, JavaScriptTypeScriptParser)

    fallback_parser = registry.get_parser("rust")
    assert isinstance(fallback_parser, FallbackTextChunker)
