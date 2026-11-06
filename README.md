# GrillMe — AI Mock Interviewer for Your Own GitHub Projects

GrillMe is an AI-powered mock technical interviewer that analyzes a candidate's public GitHub repository, builds a repository-grounded knowledge base using RAG, and conducts an adaptive, evidence-based technical interview orchestrated by LangGraph.

---

## Current Status: Phase 1 — Repository Ingestion & Code Parsing

- **Phase 0 (Foundation & Environment):** Completed and verified.
- **Phase 1 (Repository Ingestion & Code Parsing):** Completed and verified.
  - Safe GitHub archive retrieval with Zip Slip defense.
  - File filtering (vendor, lockfile, cache, binary, and size exclusions).
  - Syntax-aware structural parsing for **Python** (AST) and **JavaScript/TypeScript** (Tree-sitter).
  - Fallback sliding-window text chunker for documentation and unsupported languages.
  - FastAPI `/api/ingest` endpoint operational.

---

## Project Structure

```
D:\grillme\
├── .env.example              # Environment variables template
├── .gitignore                # Git exclusions (caches, virtual env, secrets, evaluation corpora)
├── pyproject.toml            # Modern Python packaging configuration (PEP 518/621)
├── requirements.txt          # Production backend dependencies
├── requirements-dev.txt      # Development, linting, and testing dependencies
├── README.md                 # Project documentation & onboarding guide
├── AGENTS.md                 # Operational guidelines for AI coding agents
├── ARCHITECTURE.md           # System architecture, data flow & component design
├── DECISIONS.md              # Architecture Decision Records (ADRs)
├── EXPERIMENT_LOG.md         # Empirical RAG & ML evaluation registry
├── IDEA.md                   # Problem statement, scope & user journey
├── LEARNING_LOG.md           # Developer & student engineering journal
├── ROADMAP.md                # Phase-by-phase development plan
├── backend/                  # FastAPI backend application package
│   ├── __init__.py
│   └── app/
│       ├── __init__.py
│       ├── main.py           # FastAPI app instance, CORS middleware & routes
│       ├── core/
│       │   ├── __init__.py
│       │   └── config.py     # Pydantic Settings configuration & limits
│       ├── api/
│       │   ├── __init__.py
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── health.py # Health check route (/health & /api/health)
│       │       └── ingestion.py # Repository ingestion endpoint (/api/ingest)
│       └── ingestion/        # Ingestion & parsing pipeline
│           ├── __init__.py
│           ├── models.py     # Ingestion models, CodeChunk schema & exceptions
│           ├── github_client.py # URL validation, GitHub API metadata & zip extraction
│           ├── file_filter.py   # Exclusion rules, binary detection & language tags
│           ├── pipeline.py      # Pipeline coordinator (fetch -> filter -> parse)
│           └── parsers/      # Extensible parser suite
│               ├── __init__.py  # ParserRegistry
│               ├── base.py      # BaseCodeParser & ChunkContext
│               ├── python_parser.py # Python AST parser (functions, classes, methods)
│               ├── js_ts_parser.py  # JS/TS Tree-sitter parser
│               └── fallback_text.py # Sliding-window text chunker
└── tests/                    # Automated test suite
    ├── __init__.py
    ├── conftest.py           # TestClient fixtures
    ├── test_health.py        # Health and root endpoint tests
    ├── test_url_validation.py# GitHub URL validation tests
    ├── test_file_filter.py   # File exclusion, binary, and size filtering tests
    ├── test_parsers.py       # Python, JS/TS, and fallback chunker tests
    ├── test_safe_extraction.py # Zip Slip and archive limit tests
    ├── test_ingestion_api.py # /api/ingest endpoint integration tests
    └── test_live_smoke.py    # Opt-in live GitHub integration test (pytest -m live)
```

---

## How Repository Ingestion Works

1. **URL Validation & Normalization:** Validates that the input is a valid public GitHub URL (e.g. `https://github.com/owner/repo`). Extracts `owner` and `repo` while rejecting malformed paths, traversal attempts, or unsupported hosts.
2. **Metadata Verification:** Queries the GitHub REST API (`/repos/{owner}/{repo}`) to verify repository existence, public accessibility, default branch, stars, and non-empty status.
3. **Safe Archive Retrieval:** Downloads a compressed zipball of the repository at its default branch via a streaming client, strictly enforcing archive size limits.
4. **Sandboxed Extraction:** Extracts the archive in an isolated temporary directory with built-in **Zip Slip defense** (rejecting relative path escapes, absolute paths, or invalid symbols) and automatic cleanup upon exit.
5. **Noise Filtering:** Inspects every file path against exclusion rules: vendor directories (`node_modules/`, `venv/`), lockfiles, caches, minified assets, and binary formats. Probes file headers for null bytes.
6. **Syntax-Aware Parsing & Chunking:** Passes selected files to the parser registry:
   - Python files are parsed using Python's native `ast` to extract classes, functions, and methods with 1-based line ranges and decorators.
   - JavaScript/TypeScript files are parsed via **Tree-sitter** (`tree-sitter-javascript`, `tree-sitter-typescript`) into semantic function, class, and export blocks.
   - Documentation and unsupported file types are chunked deterministically using the **Fallback Text Chunker** (sliding line window with configurable overlap).
7. **Chunk Model Generation:** Produces normalized `CodeChunk` objects containing repository citations, relative file paths, line ranges, symbols, and language tags.

---

## Supported Initial Languages

| Language | Extensions | Parser Engine | Extracted Units |
|---|---|---|---|
| **Python** | `.py`, `.pyi` | Python `ast` | Functions, Async Functions, Classes, Methods, Module blocks |
| **JavaScript** | `.js`, `.jsx`, `.mjs`, `.cjs` | Tree-sitter | Function declarations, Classes, Arrow functions, Exports |
| **TypeScript** | `.ts`, `.tsx`, `.mts`, `.cts` | Tree-sitter | Typed functions, Classes, TSX components, Exports |
| **Documentation** | `.md`, `.markdown`, `.rst`, `.txt`, `README` | Fallback Chunker | Line-bounded text chunks (50-line window, 10-line overlap) |
| **Configs / Others** | `.json`, `.toml`, `.yaml`, `.sql`, `.go`, etc. | Fallback Chunker | Line-bounded text chunks |

---

## File Filtering & Safety Exclusions

Files are excluded from ingestion if they match any of the following criteria:
- **Excluded Directories:** `.git/`, `.github/`, `node_modules/`, `.venv/`, `venv/`, `env/`, `__pycache__/`, `dist/`, `build/`, `.pytest_cache/`, `.mypy_cache/`, `htmlcov/`, `.idea/`, `.vscode/`, `vendor/`, etc.
- **Lockfiles & Minified Assets:** `package-lock.json`, `yarn.lock`, `poetry.lock`, `pnpm-lock.yaml`, `Cargo.lock`, `go.sum`, `*.min.js`, `*.min.css`.
- **Binary & Media Formats:** `.png`, `.jpg`, `.pdf`, `.zip`, `.exe`, `.so`, `.dll`, `.pyc`, `.whl`, `.db`, `.sqlite`, `.woff2`, `.mp4`, etc.
- **Content Inspection:** Files containing binary null bytes (`\x00`) in their initial header or failing UTF-8 decoding.
- **Size Safeguards:** Files larger than `MAX_FILE_SIZE_BYTES` (default: 100 KB) or empty files (0 bytes).

---

## Chunk Metadata Schema

Every generated `CodeChunk` contains:
```json
{
  "repo_owner": "torvalds",
  "repo_name": "linux",
  "repo_url": "https://github.com/torvalds/linux",
  "branch_or_commit": "master",
  "file_path": "kernel/sched/core.c",
  "language": "c",
  "content": "... exact source code lines ...",
  "chunk_index": 0,
  "start_line": 45,
  "end_line": 95,
  "symbol_name": "schedule",
  "chunk_type": "function"
}
```

---

## Ingestion API Usage

### Endpoint: `POST /api/ingest`

#### Example Request:
```bash
curl -X POST http://127.0.0.1:8000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/fastapi/fastapi"}'
```

#### Example Response:
```json
{
  "status": "success",
  "repository": {
    "owner": "fastapi",
    "name": "fastapi",
    "full_name": "fastapi/fastapi",
    "url": "https://github.com/fastapi/fastapi",
    "default_branch": "master",
    "description": "FastAPI framework, high performance, easy to learn, fast to code, ready for production",
    "stars": 78000,
    "commit_sha": null
  },
  "files_discovered": 142,
  "files_selected": 98,
  "files_skipped": 44,
  "chunks_produced": 412,
  "warnings": [],
  "duration_ms": 1240.5
}
```

#### Error Status Codes:
- `400 Bad Request`: Malformed or unsupported URL.
- `404 Not Found`: Repository not found on GitHub or private.
- `413 Content Too Large`: Repository archive or file count exceeds safety limits.
- `422 Unprocessable Content`: Repository is empty or has no eligible source files.
- `429 Too Many Requests`: GitHub API unauthenticated rate limit reached.

---

## Configurable Limits (`.env`)

Configure safety thresholds in `.env` (copied from `.env.example`):

```ini
# Maximum repository archive download size in bytes (default: 50 MB)
MAX_REPO_SIZE_BYTES=52428800

# Maximum eligible files processed per repository (default: 500)
MAX_FILE_COUNT=500

# Maximum size per individual file in bytes (default: 100 KB)
MAX_FILE_SIZE_BYTES=102400

# Line window and overlap for fallback text chunker
CHUNK_SIZE_LINES=50
CHUNK_OVERLAP_LINES=10

# Optional GitHub Personal Access Token (raises rate limits from 60/hr to 5,000/hr)
# GITHUB_TOKEN=ghp_your_token_here
```

---

## Known Limitations (v1 Scope)

- **Public Repositories Only:** Private repositories requiring OAuth are not supported in v1.
- **Zero Code Execution:** GrillMe never executes, builds, or tests repository code.
- **Initial First-Class Structural Parsing:** Python and JavaScript/TypeScript have AST/Tree-sitter structural parsing. Other languages (Go, Rust, Java, C++) use the fallback text chunker in v1.

---

## Local Setup & Development Guide (Windows 11 / PowerShell)

### 1. Virtual Environment & Dependencies
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install all production and development dependencies
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

### 2. Run Automated Unit & Integration Tests
```powershell
# Run the standard offline test suite (33 tests, ~0.2s)
pytest

# Optional: Run the live GitHub integration test (requires active internet access)
pytest -m live
```

### 3. Code Quality & Typing Checks
```powershell
# Run Ruff linter
ruff check .

# Run Mypy strict type checker
mypy backend tests
```

### 4. Start the FastAPI Development Server
```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```
Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to test the `/api/health` and `/api/ingest` endpoints interactively.
