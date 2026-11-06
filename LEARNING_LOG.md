# GrillMe — Developer Learning Log

This document serves as an ongoing learning journal for developers and students building **GrillMe**. As you implement each phase, record key conceptual discoveries, technical decisions, debugging journeys, and open questions here.

> **Instruction:** Do not fabricate historical entries. Add a new entry whenever you work on a task, encounter an error, or learn a new concept.

---

## Learning Log Entry Template

Copy and paste the template below to document each session or milestone:

```markdown
### [YYYY-MM-DD] — [Brief Title: Phase or Topic]

- **Author / Contributor:** [Your Name / Handle]
- **Relevant Phase:** [e.g., Phase 0, Phase 1, Phase 2, etc.]

#### 1. Concepts Learned
- [Key concept 1, e.g., how AST parsing handles nested closures in Python]
- [Key concept 2, e.g., how LangGraph checkpointing preserves conversation state across HTTP turns]

#### 2. Implementation Notes & Technical Discoveries
- [Note 1: Technical nuances, library behaviors, or unexpected API quirks discovered]
- [Note 2: Architectural insights or patterns implemented]

#### 3. Errors Encountered & How They Were Resolved
- **Error:** `[Paste exact error message or describe unexpected behavior]`
  - **Root Cause:** `[Explain why the error occurred]`
  - **Solution / Fix:** `[Explain how it was resolved]`

#### 4. Open Questions to Revisit
- [ ] [Question or edge case that needs further research or testing later]
- [ ] [Potential optimization to explore when scaling]
```

---

## Log Entries

### [2026-11-03] — Phase 0: Project Foundation & Minimal Backend Setup

- **Author / Contributor:** Agent & User Team
- **Relevant Phase:** Phase 0 (Checkpoints 0.1 – 0.6)

#### 1. Concepts Learned
- **FastAPI Application Decoupling:** Setting up modular FastAPI routes with `APIRouter` allows mounting the health endpoint at both `/health` and `/api/health` cleanly without code duplication.
- **Generator Fixture Typing in Pytest:** Pytest fixtures yielding a client (such as `TestClient`) require typing annotations like `Generator[TestClient, None, None]` or `Iterator[TestClient]` under strict Mypy checking.
- **Git Remote State Verification:** Using `git ls-remote <url>` allows non-destructive inspection of a remote GitHub repository's ref state before initializing or pushing from a local directory.

#### 2. Implementation Notes & Technical Discoveries
- Successfully initialized local Git repository on branch `main` and linked remote `origin` to `https://github.com/obj8899/GrillMe` after confirming the remote repository is completely empty.
- Pinned and installed foundation backend dependencies (`fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `pytest`, `httpx`, `ruff`, `mypy`) in Python 3.13.5 virtual environment.
- Configured `.gitignore` to protect raw/processed evaluation corpora, benchmark outputs, and local SQLite databases in addition to standard Python and virtual environment exclusions.

#### 3. Errors Encountered & How They Were Resolved
- **Error:** `tests\conftest.py:10: error: The return type of a generator function should be "Generator" or one of its supertypes  [misc]`
  - **Root Cause:** In `conftest.py`, the `client()` fixture used `yield test_client` but had return type annotation `-> TestClient`.
  - **Solution / Fix:** Imported `Generator` from `collections.abc` and updated the return type to `Generator[TestClient, None, None]`. Mypy re-run confirmed 100% type safety across all 11 source files.

#### 4. Open Questions to Revisit
- [ ] Verify LangGraph SQLite checkpointer package name and API when entering Phase 3.
- [ ] Evaluate AST parsing libraries (e.g., Tree-sitter vs. Python `ast`) for Phase 1 chunking.
### [2026-11-06] — Phase 1: Repository Ingestion & Code Parsing Pipeline

- **Author / Contributor:** Agent & User Team
- **Relevant Phase:** Phase 1

#### 1. Concepts Learned
- **Tree-sitter Python Bindings:** In modern Tree-sitter (0.22+), language grammars are distributed as dedicated prebuilt packages (`tree-sitter-javascript`, `tree-sitter-typescript`). They parse both standard JS and TypeScript/TSX into concrete syntax trees without requiring a Node.js runtime.
- **Zip Slip Defense:** Validating archive filenames using `Path.resolve().relative_to(target_dir)` and checking for `..` segments prevents malicious directory traversal when unpacking untrusted zip files.
- **Extensionless Text Detection:** Real-world repositories frequently include files without extensions (e.g., `README`, `LICENSE`, `Dockerfile`, `Makefile`). Explicitly mapping these filenames ensures essential documentation is not discarded during filtering.

#### 2. Implementation Notes & Technical Discoveries
- Implemented an extensible parsing architecture with `BaseCodeParser` and `ParserRegistry`, supporting AST extraction for Python, Tree-sitter for JS/TS, and a sliding-window fallback chunker for documentation.
- Integrated GitHub API streaming archive retrieval in `GitHubClient`, strictly enforcing size and file count caps to guard against Denial of Service.
- Mounted the `/api/ingest` endpoint on FastAPI with structured error mapping (400, 404, 413, 422, 429).
- Separated live network integration tests using `@pytest.mark.live` and configured `pyproject.toml` to deselect live tests by default (`-m 'not live'`), ensuring the test suite remains fast, isolated, and deterministic.

#### 3. Errors Encountered & How They Were Resolved
- **Error:** `tests/test_safe_extraction.py:58: AssertionError: assert 'safe.py' in ['myorg-myrepo-a1b2c3d/safe.py']`
  - **Root Cause:** When zip archives contained mixed entries (some with GitHub prefixes and some malicious traversal attempts), a strict `all(name.startswith(prefix))` check failed to detect the legitimate archive folder prefix.
  - **Solution / Fix:** Updated prefix detection in `extract_zipball_safely` to identify the first valid non-dot directory segment, correctly stripping the container prefix from legitimate repository files while neutralizing traversal attempts.

#### 4. Open Questions to Revisit
- [ ] For Phase 2 (RAG & Indexing), design the `VectorStore` abstraction interface to ingest `list[CodeChunk]` with metadata embeddings directly.
- [ ] Evaluate ChromaDB embedding model options (e.g. `all-MiniLM-L6-v2` vs. OpenAI `text-embedding-3-small`).
