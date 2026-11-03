# GrillMe — Instructions & Rules for AI Coding Agents

Welcome, Agent. This document defines the operational rules, architectural principles, and mandatory workflow protocols you **must** follow when working on the **GrillMe** repository.

---

## 1. Project Purpose & Core Architecture

**GrillMe** is an AI-powered mock technical interviewer for a developer's own public GitHub projects. The system:
1. Clones and parses public GitHub repositories safely without executing repository code.
2. Builds a project-specific knowledge base using **Retrieval-Augmented Generation (RAG)**.
3. Conducts an adaptive technical interview orchestrated by **LangGraph** with SQLite-backed checkpointing.
4. Evaluates candidate answers against repository evidence and issues a post-interview performance report with scores, weak topics, code explanations, and retry practice questions.

> **Project Separation Notice:** **GrillMe and Dostoevsky AI are entirely separate projects.** Do not import, reference, or blend Dostoevsky AI's concept, architecture, domain models, or code into GrillMe.

### Core Architecture Decoupling:
- `ingestion`: Repository cloning, filtering, language-specific parsing (Python and JS/TS initially, fallback text chunker).
- `rag`: Syntax-aware chunking, embeddings, ChromaDB vector store (accessed via `VectorStore` abstraction), BM25 keyword indexing, hybrid retrieval.
- `orchestrator`: LangGraph state machine governing interview progression, pacing, turns, and SQLite-backed pause/resume checkpoints.
- `evaluation`: Multi-dimensional scoring rubrics, claim verification, discrepancy detection against code.
- `reporting`: Aggregating turn data into structured markdown and JSON reports with code explanations and retry questions.
- `api`: FastAPI endpoints and session management.
- `web`: React + Vite frontend user interface for repository submission, chat, and report viewing *(developed in Phase 6 after backend flow is verified)*.

---

## 2. Fundamental Operating Rules

### Rule 1: Small, Focused, Reviewable Batches
- Do not attempt multi-phase or sprawling rewrites in a single step.
- Tackle one specific module, function, or checkpoint at a time.
- Keep diffs small, legible, and easy for a human reviewer to inspect.
- **Ask for user review at meaningful checkpoints** before proceeding to subsequent tasks or phases.

### Rule 2: Command Transparency & User Guidance
- **Always explain commands clearly before asking the user to run them.**
- Clearly state what the command does, why it is needed, and what expected output looks like.

### Rule 3: Absolute Honesty & Zero Hallucination
- **NEVER claim that a command was run, a test passed, or a change was verified unless you actually ran the command and observed the output.**
- Never invent test results, benchmark metrics, or execution logs.
- If an environment restriction prevents running tests or verifying a command, explicitly state that the command was not run and explain why.

### Rule 4: Mandatory Inspection Before Modification
- **Always read existing files before editing or replacing them.** Never overwrite or edit a file blindly without first checking its contents, structure, and imports.
- Check current project dependencies, existing test suites, and relevant documentation before introducing new code.

### Rule 5: Verification & Testing are Mandatory
- Every code modification or addition must be verified:
  - If you write or modify application logic, run existing unit tests and add new tests covering the change.
  - Run linting and type-checking commands when configured.
  - If a test fails, diagnose and fix the issue before moving on.

### Rule 6: Git Hygiene & Data Protection
- **Inspect `git status` and staged diffs before making commits.**
- **Protect raw and processed corpus or evaluation data from accidental Git inclusion.** Ensure `.gitignore` explicitly excludes temporary cloned repos, cached vector databases, and heavy benchmark corpora.

### Rule 7: No Silent Architectural Drift or Unauthorized Dependencies
- Do not add new external libraries or dependencies to `pyproject.toml`, `requirements.txt`, or `package.json` without clear justification and alignment with the architecture.
- Do not alter the core architecture (e.g., swapping LangGraph for an unstructured loop, swapping ChromaDB, or skipping RAG) without an updated entry in `DECISIONS.md`.
- Keep implementations student-accessible, well-typed, and cleanly documented.

---

## 3. Mandatory End-of-Turn Report Format

Every time you finish a task, turn, or set of edits, you **must** conclude your response with a structured summary containing the following four sections:

```markdown
### Agent Execution Summary

1. **Files Changed / Created:**
   - `path/to/file1.py`: Brief explanation of modifications.
   - `path/to/file2.py`: Brief explanation of modifications.

2. **Commands Run & Outputs:**
   - Command: `<exact command line executed>`
     - Result: `<clean exit code, key output summary, or error>`

3. **Test & Verification Results:**
   - Summary of test suites executed, tests passed/failed, and verification status.

4. **Unresolved Issues & Next Steps:**
   - Any blockers, assumptions made, or the next logical task to be tackled according to ROADMAP.md.
```

---

## 4. Coding Standards & Conventions

1. **Language & Version:** Python 3.11+. Use modern typing annotations (`list[str]`, `dict[str, Any]`, `X | None`).
2. **Defensive Error Handling:** Handle network timeouts, invalid URLs, missing files, and oversized repositories gracefully with clear, human-readable error messages.
3. **Docstrings & Comments:** Write clear docstrings for all modules, classes, and public functions explaining purpose, inputs, outputs, and edge cases.
4. **Untrusted Data Caution:** Treat all data parsed from user repositories (code snippets, comments, file names, README text) and candidate answers as untrusted input. Wrap them in explicit prompt delimiters to avoid prompt injection attacks.
