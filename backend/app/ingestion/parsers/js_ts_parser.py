"""Syntax-aware JavaScript and TypeScript parser using Tree-sitter."""

from pathlib import Path

import tree_sitter_javascript
import tree_sitter_typescript
from tree_sitter import Language, Node, Parser

from backend.app.ingestion.models import CodeChunk
from backend.app.ingestion.parsers.base import BaseCodeParser, ChunkContext
from backend.app.ingestion.parsers.fallback_text import FallbackTextChunker


class JavaScriptTypeScriptParser(BaseCodeParser):
    """Parses JavaScript and TypeScript into structured AST code chunks using Tree-sitter."""

    def __init__(self, fallback_chunker: FallbackTextChunker | None = None) -> None:
        self.fallback = fallback_chunker or FallbackTextChunker()

        # Initialize language grammars
        self.js_lang = Language(tree_sitter_javascript.language())
        self.ts_lang = Language(tree_sitter_typescript.language_typescript())
        self.tsx_lang = Language(tree_sitter_typescript.language_tsx())

        # Initialize parser instances
        self.js_parser = Parser(self.js_lang)
        self.ts_parser = Parser(self.ts_lang)
        self.tsx_parser = Parser(self.tsx_lang)

    def can_parse(self, language: str) -> bool:
        return language in ("javascript", "typescript")

    def _select_parser(self, file_path: str, language: str) -> Parser:
        suffix = Path(file_path).suffix.lower()
        if suffix == ".tsx":
            return self.tsx_parser
        elif suffix in (".ts", ".mts", ".cts"):
            return self.ts_parser
        return self.js_parser

    def _extract_symbol_info(self, node: Node) -> tuple[str | None, str]:
        """Determine symbol name and chunk type ('function' or 'class') from an AST node."""
        actual_node = node

        # If wrapped in an export statement, examine the inner declaration
        if node.type == "export_statement":
            decl = node.child_by_field_name("declaration")
            if decl is not None:
                actual_node = decl

        if actual_node.type == "function_declaration":
            name_node = actual_node.child_by_field_name("name")
            name = name_node.text.decode("utf-8") if name_node and name_node.text else None
            return name, "function"

        elif actual_node.type == "class_declaration":
            name_node = actual_node.child_by_field_name("name")
            name = name_node.text.decode("utf-8") if name_node and name_node.text else None
            return name, "class"

        elif actual_node.type in ("lexical_declaration", "variable_declaration"):
            # Check for const myFunc = () => { ... } or const Comp = function() { ... }
            for child in actual_node.children:
                if child.type == "variable_declarator":
                    val_node = child.child_by_field_name("value")
                    if val_node and val_node.type in ("arrow_function", "function_expression"):
                        name_node = child.child_by_field_name("name")
                        name = (
                            name_node.text.decode("utf-8")
                            if name_node and name_node.text
                            else None
                        )
                        return name, "function"

        return None, "module"

    def parse(self, content: str, context: ChunkContext) -> list[CodeChunk]:
        """Extract functions, classes, and module-level code from JS/TS source."""
        if not content or not content.strip():
            return []

        lines = content.splitlines()
        total_lines = len(lines)
        if total_lines == 0:
            return []

        parser = self._select_parser(context.file_path, context.language)
        try:
            tree = parser.parse(content.encode("utf-8"))
        except Exception:
            return self.fallback.parse(content, context)

        root = tree.root_node
        if not root or not root.children:
            return self.fallback.parse(content, context)

        chunks: list[CodeChunk] = []
        covered_lines: set[int] = set()

        def extract_slice(start_line: int, end_line: int) -> str:
            start_idx = max(0, start_line - 1)
            end_idx = min(total_lines, end_line)
            return "\n".join(lines[start_idx:end_idx]).strip()

        # Iterate top-level AST nodes
        for node in root.children:
            symbol_name, chunk_type = self._extract_symbol_info(node)
            if chunk_type in ("function", "class"):
                start = node.start_point.row + 1
                end = node.end_point.row + 1
                chunk_code = extract_slice(start, end)
                if chunk_code:
                    chunks.append(
                        CodeChunk(
                            repo_owner=context.repo_owner,
                            repo_name=context.repo_name,
                            repo_url=context.repo_url,
                            branch_or_commit=context.branch_or_commit,
                            file_path=context.file_path,
                            language=context.language,
                            content=chunk_code,
                            chunk_index=len(chunks),
                            start_line=start,
                            end_line=end,
                            symbol_name=symbol_name,
                            chunk_type=chunk_type,
                        )
                    )
                    covered_lines.update(range(start, end + 1))

        # Extract remaining top-level module statements (imports, exports, configs)
        uncovered_lines = sorted(set(range(1, total_lines + 1)) - covered_lines)
        if uncovered_lines:
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
                block_code = extract_slice(b_start, b_end)
                if block_code and len(block_code.strip()) > 10:
                    chunks.append(
                        CodeChunk(
                            repo_owner=context.repo_owner,
                            repo_name=context.repo_name,
                            repo_url=context.repo_url,
                            branch_or_commit=context.branch_or_commit,
                            file_path=context.file_path,
                            language=context.language,
                            content=block_code,
                            chunk_index=len(chunks),
                            start_line=b_start,
                            end_line=b_end,
                            symbol_name=None,
                            chunk_type="module",
                        )
                    )

        # Normalize ordering and sequential indexing
        chunks.sort(key=lambda c: (c.start_line or 0))
        for idx, chunk in enumerate(chunks):
            chunks[idx] = chunk.model_copy(update={"chunk_index": idx})

        if not chunks:
            return self.fallback.parse(content, context)

        return chunks
