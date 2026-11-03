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
