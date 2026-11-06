"""File filtering logic for selecting source code and documentation while excluding noise."""

from dataclasses import dataclass
from pathlib import Path

from backend.app.core.config import settings

# Common directory names to exclude unconditionally
EXCLUDED_DIRECTORY_NAMES = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "htmlcov",
    ".tox",
    ".idea",
    ".vscode",
    "vendor",
    "eggs",
    ".eggs",
    "wheels",
    "target",
    "bin",
    "obj",
    ".next",
    ".nuxt",
}

# File extensions indicating non-text binary files or assets
BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".webp",
    ".bmp",
    ".pdf",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".7z",
    ".rar",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".pyc",
    ".pyo",
    ".pyd",
    ".whl",
    ".bin",
    ".dat",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".mp3",
    ".mp4",
    ".mov",
    ".avi",
    ".wasm",
}

# Machine-generated lockfiles and minified files to exclude
EXCLUDED_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "composer.lock",
    "Cargo.lock",
    "go.sum",
    "Pipfile.lock",
}

# Known filenames without extensions that should be included
SPECIAL_FILENAMES: dict[str, str] = {
    "readme": "markdown",
    "license": "text",
    "dockerfile": "dockerfile",
    "makefile": "makefile",
}

# Mapping of file extension to canonical language tag
EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    # Python
    ".py": "python",
    ".pyi": "python",
    # JavaScript
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    # TypeScript
    ".ts": "typescript",
    ".tsx": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    # Documentation
    ".md": "markdown",
    ".markdown": "markdown",
    ".rst": "rst",
    ".txt": "text",
    # General source & configs (use fallback text chunker)
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".sh": "shell",
    ".bash": "shell",
    ".go": "go",
    ".java": "java",
    ".rs": "rust",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
}


@dataclass(frozen=True)
class FilterDecision:
    """Result of evaluating a file against ingestion filtering criteria."""

    selected: bool
    language: str | None = None
    reason: str | None = None


class FileFilter:
    """Evaluates files for ingestion suitability based on path, size, and content."""

    def __init__(
        self,
        max_file_size_bytes: int = settings.max_file_size_bytes,
    ) -> None:
        self.max_file_size_bytes = max_file_size_bytes

    def evaluate_path(self, relative_path: str) -> FilterDecision:
        """First-stage check: evaluate directory hierarchy, filename, and extension."""
        path_obj = Path(relative_path)
        parts = path_obj.parts

        # 1. Directory exclusion check
        for part in parts[:-1]:
            if part.lower() in EXCLUDED_DIRECTORY_NAMES or part.startswith("."):
                return FilterDecision(
                    selected=False,
                    reason=f"File resides in excluded directory '{part}'",
                )

        filename = path_obj.name.lower()

        # 2. Excluded filenames (e.g. lockfiles, minified files)
        if filename in EXCLUDED_FILENAMES:
            return FilterDecision(
                selected=False,
                reason=f"Excluded manifest/lockfile '{filename}'",
            )
        if filename.endswith(".min.js") or filename.endswith(".min.css"):
            return FilterDecision(
                selected=False,
                reason="Minified asset file excluded",
            )

        # 3. Hidden files (e.g. .DS_Store, .gitignore - keep README or configs)
        if filename.startswith(".") and not filename.startswith(".env.example"):
            return FilterDecision(
                selected=False,
                reason="Hidden configuration or system file",
            )

        # 4. Binary extension check
        ext = path_obj.suffix.lower()
        if ext in BINARY_EXTENSIONS:
            return FilterDecision(
                selected=False,
                reason=f"Binary file extension '{ext}'",
            )

        # 5. Language mapping
        ext = path_obj.suffix.lower()
        if not ext and filename in SPECIAL_FILENAMES:
            return FilterDecision(selected=True, language=SPECIAL_FILENAMES[filename])

        language = EXTENSION_LANGUAGE_MAP.get(ext)
        if not language:
            return FilterDecision(
                selected=False,
                reason=f"Unsupported file extension '{ext}'",
            )

        return FilterDecision(selected=True, language=language)

    def evaluate_file(self, relative_path: str, file_path: Path) -> FilterDecision:
        """Second-stage check: evaluate on-disk file size and textual decodeability."""
        path_decision = self.evaluate_path(relative_path)
        if not path_decision.selected:
            return path_decision

        try:
            stat_result = file_path.stat()
            file_size = stat_result.st_size

            # Empty file check
            if file_size == 0:
                return FilterDecision(
                    selected=False,
                    reason="File is empty (0 bytes)",
                )

            # Oversized file check
            if file_size > self.max_file_size_bytes:
                return FilterDecision(
                    selected=False,
                    reason=(
                        f"File size ({file_size} bytes) exceeds limit "
                        f"({self.max_file_size_bytes} bytes)"
                    ),
                )

            # Binary content check: probe first 1024 bytes for null bytes
            with open(file_path, "rb") as f:
                sample = f.read(1024)
                if b"\x00" in sample:
                    return FilterDecision(
                        selected=False,
                        reason="Binary null bytes detected in file header",
                    )

            return FilterDecision(
                selected=True,
                language=path_decision.language,
            )

        except Exception as exc:
            return FilterDecision(
                selected=False,
                reason=f"Failed to read file from disk: {exc}",
            )
