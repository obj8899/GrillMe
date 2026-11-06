"""Python AST-based structural code parser extracting classes, functions, and methods."""

import ast
from typing import Any

from backend.app.ingestion.models import CodeChunk
from backend.app.ingestion.parsers.base import BaseCodeParser, ChunkContext
from backend.app.ingestion.parsers.fallback_text import FallbackTextChunker


class PythonParser(BaseCodeParser):
    """Parses Python source files into structured AST code chunks."""

    def __init__(self, fallback_chunker: FallbackTextChunker | None = None) -> None:
        self.fallback = fallback_chunker or FallbackTextChunker()

    def can_parse(self, language: str) -> bool:
        return language == "python"

    def _get_node_start_line(self, node: ast.AST) -> int:
        """Get 1-based start line, factoring in decorators if present."""
        decorator_list = getattr(node, "decorator_list", None)
        if decorator_list:
            return int(min(d.lineno for d in decorator_list))
        return int(getattr(node, "lineno", 1))

    def _get_node_end_line(self, node: ast.AST, default: int) -> int:
        """Get 1-based end line of an AST node."""
        end_lineno = getattr(node, "end_lineno", None)
        return int(end_lineno) if end_lineno is not None else default

    def parse(self, content: str, context: ChunkContext) -> list[CodeChunk]:
        """Extract classes, methods, functions, and module-level code from Python source."""
        if not content or not content.strip():
            return []

        lines = content.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return []

        try:
            tree = ast.parse(content, filename=context.file_path)
        except SyntaxError:
            # On syntax error in target repo, fall back to sliding-window text chunker
            return self.fallback.parse(content, context)

        chunks: list[CodeChunk] = []
        covered_lines: set[int] = set()

        def extract_slice(start_line: int, end_line: int) -> str:
            start_idx = max(0, start_line - 1)
            end_idx = min(total_lines, end_line)
            return "\n".join(lines[start_idx:end_idx]).strip()

        # 1. First pass: top-level functions and classes
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = self._get_node_start_line(node)
                end = self._get_node_end_line(node, total_lines)
                chunk_code = extract_slice(start, end)
                if chunk_code:
                    chunks.append(
                        CodeChunk(
                            repo_owner=context.repo_owner,
                            repo_name=context.repo_name,
                            repo_url=context.repo_url,
                            branch_or_commit=context.branch_or_commit,
                            file_path=context.file_path,
                            language="python",
                            content=chunk_code,
                            chunk_index=len(chunks),
                            start_line=start,
                            end_line=end,
                            symbol_name=node.name,
                            chunk_type="function",
                        )
                    )
                    covered_lines.update(range(start, end + 1))

            elif isinstance(node, ast.ClassDef):
                start = self._get_node_start_line(node)
                end = self._get_node_end_line(node, total_lines)
                class_code = extract_slice(start, end)

                # If class is relatively compact (<= 50 lines), keep as single cohesive chunk
                if end - start <= 50:
                    if class_code:
                        chunks.append(
                            CodeChunk(
                                repo_owner=context.repo_owner,
                                repo_name=context.repo_name,
                                repo_url=context.repo_url,
                                branch_or_commit=context.branch_or_commit,
                                file_path=context.file_path,
                                language="python",
                                content=class_code,
                                chunk_index=len(chunks),
                                start_line=start,
                                end_line=end,
                                symbol_name=node.name,
                                chunk_type="class",
                            )
                        )
                        covered_lines.update(range(start, end + 1))
                else:
                    # For larger classes, extract individual methods and a class header
                    method_nodes: list[Any] = [
                        item
                        for item in node.body
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]

                    # Class header chunk (class signature, docstring, class-level attributes)
                    header_end = (
                        self._get_node_start_line(method_nodes[0]) - 1
                        if method_nodes
                        else min(start + 15, end)
                    )
                    header_code = extract_slice(start, header_end)
                    if header_code:
                        chunks.append(
                            CodeChunk(
                                repo_owner=context.repo_owner,
                                repo_name=context.repo_name,
                                repo_url=context.repo_url,
                                branch_or_commit=context.branch_or_commit,
                                file_path=context.file_path,
                                language="python",
                                content=header_code,
                                chunk_index=len(chunks),
                                start_line=start,
                                end_line=header_end,
                                symbol_name=node.name,
                                chunk_type="class",
                            )
                        )
                        covered_lines.update(range(start, header_end + 1))

                    # Methods
                    for method in method_nodes:
                        m_start = self._get_node_start_line(method)
                        m_end = self._get_node_end_line(method, end)
                        m_code = extract_slice(m_start, m_end)
                        if m_code:
                            chunks.append(
                                CodeChunk(
                                    repo_owner=context.repo_owner,
                                    repo_name=context.repo_name,
                                    repo_url=context.repo_url,
                                    branch_or_commit=context.branch_or_commit,
                                    file_path=context.file_path,
                                    language="python",
                                    content=m_code,
                                    chunk_index=len(chunks),
                                    start_line=m_start,
                                    end_line=m_end,
                                    symbol_name=f"{node.name}.{method.name}",
                                    chunk_type="method",
                                )
                            )
                            covered_lines.update(range(m_start, m_end + 1))

        # 2. Extract remaining top-level module code (imports, global definitions)
        uncovered_lines = sorted(set(range(1, total_lines + 1)) - covered_lines)
        if uncovered_lines:
            # Group consecutive uncovered lines into module-level blocks
            blocks: list[tuple[int, int]] = []
            curr_start = uncovered_lines[0]
            curr_prev = uncovered_lines[0]

            for line_no in uncovered_lines[1:]:
                if line_no == curr_prev + 1:
                    curr_prev = line_no
                else:
                    blocks.append((curr_start, curr_prev))
                    curr_start = line_no
                    curr_prev = line_no
            blocks.append((curr_start, curr_prev))

            for b_start, b_end in blocks:
                # Ignore tiny whitespace-only intervals
                block_code = extract_slice(b_start, b_end)
                if block_code and len(block_code.strip()) > 10:
                    chunks.append(
                        CodeChunk(
                            repo_owner=context.repo_owner,
                            repo_name=context.repo_name,
                            repo_url=context.repo_url,
                            branch_or_commit=context.branch_or_commit,
                            file_path=context.file_path,
                            language="python",
                            content=block_code,
                            chunk_index=len(chunks),
                            start_line=b_start,
                            end_line=b_end,
                            symbol_name=None,
                            chunk_type="module",
                        )
                    )

        # Sort chunks by start_line and normalize chunk indices
        chunks.sort(key=lambda c: (c.start_line or 0))
        for idx, chunk in enumerate(chunks):
            # Re-index to ensure strictly sequential indices
            chunks[idx] = chunk.model_copy(update={"chunk_index": idx})

        # Fall back if no chunks were extracted (e.g. only comments or empty AST)
        if not chunks:
            return self.fallback.parse(content, context)

        return chunks
