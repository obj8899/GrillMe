# GrillMe — Development Roadmap

This roadmap breaks down the construction of GrillMe from absolute zero into small, disciplined, and sequential phases. Every phase defines a concrete objective, specific implementation tasks, verifiable deliverables, and rigorous verification criteria.

> **Status Notice:** Phase 0 (Foundation & Environment) is completed and verified. Implementation of Phase 1 has not started.

---

## Workstream Overview

```
[Phase 0: Foundation & Environment (Checkpoints 0.1 - 0.6)] ──► COMPLETED
               │
               ▼
[Phase 1: Ingestion & Parsing (Python, JS/TS + Fallback)]
               │
               ▼
[Phase 2: RAG & Indexing (ChromaDB via Abstraction)]
               │
               ▼
[Phase 3: LangGraph Orchestrator (SQLite Pause/Resume Checkpoints)]
               │
               ▼
[Phase 4: Answer Evaluation & Fact-Checking]
               │
               ▼
[Phase 5: Report Synthesis, Explanations & Retry Questions]
               │
               ▼
[Phase 6: Web Frontend & Chat Interface (React + Vite)]
               │
               ▼
[Phase 7: End-to-End Integration & Local Deployment]

============================================================
Continuous Workstream: Evaluation, Benchmarking & Experiments
============================================================
```

---

## Phase 0: Project Foundation & Development Environment Setup

- **Status:** *Completed*
- **Objective:** Establish the repository structure, version control linkage, isolated Python virtual environment, dependency management, baseline testing harness, Git hygiene rules, and developer documentation.

### Checkpoint 0.1: Project Structure Review & Finalization
- **Status:** *Completed*
- **Task:** Review and finalize the proposed directory layout (`backend/app/{api,core}`, `tests/`, configuration and documentation files).
- **Deliverables:** Documented and agreed directory structure reflecting the decoupled modular architecture.
- **Verification Criteria:** Clean layout specification adhering to ADR-004 with no circular dependencies. Verified.

### Checkpoint 0.2: GitHub Repository Initialization & Local Linkage
- **Status:** *Completed*
- **Task:** Initialize the Git repository locally, configure tracking to the remote GitHub repository (`https://github.com/obj8899/GrillMe`), verify `.gitignore` excludes virtual environments, IDE files, environment secrets, temporary cloned repos, and protects raw/processed corpus or benchmark evaluation data from accidental Git inclusion.
- **Deliverables:** Git repository initialized and connected to the GitHub remote repository with clean working tree.
- **Verification Criteria:** `git status` reports clean working directory; remote repository origin is correctly configured; ignore rules cover data, clones, and secrets. Verified.

### Checkpoint 0.3: Python & Virtual Environment Setup
- **Status:** *Completed*
- **Task:** Verify Python 3.11+ installation (Python 3.13.5 active), create an isolated virtual environment (`.venv`), and document activation commands across operating systems.
- **Deliverables:** Active local virtual environment (`.venv`).
- **Verification Criteria:** `python --version` outputs Python 3.11 or higher within the activated virtual environment. Verified (Python 3.13.5).

### Checkpoint 0.4: Minimal Backend Package & Configuration
- **Status:** *Completed*
- **Task:** Create minimal backend package configuration (`pyproject.toml`, `requirements.txt`, `requirements-dev.txt`), define core development tools (`fastapi`, `uvicorn`, `pytest`, `ruff`, `mypy`), and add `.env.example` for environment variable templates.
- **Deliverables:** Package configuration file and environment template in project root.
- **Verification Criteria:** Package configuration parses cleanly; linter (`ruff`) and type-checker (`mypy`) execute without configuration errors. Verified.

### Checkpoint 0.5: Basic Test Harness & Sanity Verification
- **Status:** *Completed*
- **Task:** Set up `pytest` test runner harness under `tests/` and add automated health and root endpoint sanity tests.
- **Deliverables:** Executable test suite in `tests/test_health.py`.
- **Verification Criteria:** `pytest` runs and passes with 100% exit code 0. Verified (3 passed in 0.05s).

### Checkpoint 0.6: Exact Local Setup Documentation
- **Status:** *Completed*
- **Task:** Document the exact step-by-step local setup process in `README.md` (cloning, virtual environment creation, activation, dependency installation, running tests, and starting FastAPI).
- **Deliverables:** Comprehensive onboarding section in `README.md`.
- **Verification Criteria:** A developer following `README.md` from scratch can activate the environment and execute the test suite without undocumented steps. Verified.

---

## Phase 1: Repository Ingestion & Code Parsing Pipeline

- **Status:** *Not Started*
- **Objective:** Build an isolated ingestion service that accepts a public GitHub URL, clones the repository safely into a temporary directory without executing code, filters non-code assets, and parses code with initial syntax-aware support for Python and JavaScript/TypeScript plus an extensible fallback sliding-window text chunker.
- **Implementation Tasks:**
  - Implement Git fetcher to clone public repositories into a sandboxed temporary directory with automatic cleanup.
  - Implement repository URL validation and size/file count safety limits.
  - Implement file exclusion filters (ignoring `.git/`, binary files, assets, `node_modules/`, `venv/`, lockfiles).
  - Implement extensible chunker base interface (`BaseCodeChunker`).
  - Implement syntax-aware chunkers for **Python** (`.py`) and **JavaScript/TypeScript** (`.js`, `.jsx`, `.ts`, `.tsx`), preserving class, function, and module boundaries.
  - Implement fallback sliding-window text chunker for documentation and unsupported languages.
  - Extract high-level repository summary and directory tree structure.
- **Expected Deliverables:**
  - Module: `src/grillme/ingestion/` (or `backend/app/ingestion/`) containing fetcher, cleaner, structural parsers, and fallback chunker.
  - Unit tests with mock repositories verifying exclusion filters, size limits, Python/TS AST chunking, and fallback behavior.
- **Verification Criteria:**
  - Running ingestion against sample Python and TypeScript repos extracts function/class chunks with accurate line ranges and metadata headers.
  - Non-code files and lockfiles are completely excluded.
  - Cloned temporary directories are purged after processing.
  - Zero repository code is executed during ingestion.

---

## Phase 2: RAG Pipeline & Code Knowledge Base Indexing

- **Status:** *Not Started*
- **Objective:** Transform chunked code into a searchable knowledge base using ChromaDB as the sole initial local vector store behind a storage abstraction, combined with BM25 keyword search.
- **Implementation Tasks:**
  - Define a clean, minimal `VectorStore` abstraction interface for adding chunks, querying similarity, and filtering metadata.
  - Implement the **ChromaDB** adapter implementing the `VectorStore` interface for local/embedded development. *(Do not implement Qdrant or other vector stores in v1).*
  - Implement embedding generator wrapper supporting pluggable providers (e.g., OpenAI, Gemini, Anthropic) via environment configuration.
  - Implement BM25 / keyword index for exact symbol and identifier search.
  - Implement hybrid retriever combining ChromaDB dense search with BM25 keyword search using Reciprocal Rank Fusion (RRF).
- **Expected Deliverables:**
  - Module: `src/grillme/rag/` (or `backend/app/rag/`) containing `VectorStore` interface, ChromaDB adapter, embedding wrapper, BM25 index, and hybrid retriever.
  - Integration tests verifying exact symbol lookups and semantic concept queries return expected code chunks.
- **Verification Criteria:**
  - Query for a known function name returns the exact file and line range in top-3 results.
  - Switching or mocking the `VectorStore` implementation requires zero changes to the retrieval or orchestrator logic.

---

## Phase 3: LangGraph Interview State Machine & Orchestrator

- **Status:** *Not Started*
- **Objective:** Implement the stateful interview controller using LangGraph to govern interview stages, pacing, topic progression, and turn management, featuring SQLite-backed persistence to support pause/checkpoint/resume cycles across server restarts.
- **Implementation Tasks:**
  - Define the `InterviewState` schema (tracking session ID, thread ID, repo profile, topic list, turn index, conversation history, and evaluations).
  - Implement `initialize_interview` node to generate 3–5 core technical topics from the repo profile.
  - Implement `generate_question` node to formulate targeted questions grounded in retrieved code.
  - Configure the **SQLite-backed checkpointer** (verifying the exact LangGraph checkpointer package and API for the installed version) to persist graph execution state across turns and process restarts.
  - Keep graph checkpoints separate from relational session metadata. (Reserve `MemorySaver` solely for isolated unit tests).
  - Implement pause/interrupt boundary: persist state to SQLite checkpointer and yield control to API.
  - Implement resume transition: accept candidate answer from API, load checkpointed state, and resume graph execution.
  - Implement state transition conditional edges (deciding whether to probe deeper on a topic or advance).
  - Implement turn limit guards and wrap-up transition.
- **Expected Deliverables:**
  - Module: `src/grillme/orchestrator/` (or `backend/app/orchestrator/`) with compiled LangGraph workflow and SQLite checkpointer integration.
  - Concrete automated pause/resume test simulating candidate turns over multiple HTTP-style interruptions and server restarts.
- **Verification Criteria:**
  - **Pause/Resume Test with SQLite Checkpointer Passes:** Test explicitly verifies that the graph halts after generating a question, successfully persists checkpointed state in SQLite, reloads state when a candidate answer is delivered, and resumes execution seamlessly to evaluation.
  - State survives simulated process restart without data corruption.

---

## Phase 4: Answer Evaluation & Evidence-Based Fact-Checking

- **Status:** *Not Started*
- **Objective:** Create the evaluation and fact-checking engine that compares a candidate's verbal claims against retrieved code evidence to detect inaccuracies or hand-waving using a fixed grading rubric.
- **Implementation Tasks:**
  - Implement claim extraction query generator to pull technical assertions from candidate answers.
  - Implement evaluation prompt scoring answers across fixed rubric dimensions:
    - Technical Accuracy (1–5)
    - Implementation Depth (1–5)
    - Architectural Clarity (1–5)
    - Edge Case Awareness (1–5)
  - Implement discrepancy detection: flag when a candidate claims an implementation detail that contradicts the actual codebase.
  - Identify weak topics and generate targeted feedback, code explanations, and potential retry questions.
  - Connect evaluator output to LangGraph state to trigger adaptive follow-up probes when responses are vague or inaccurate.
- **Expected Deliverables:**
  - Module: `src/grillme/evaluation/` (or `backend/app/evaluation/`) containing evaluator, claim extractor, and rubrics.
  - Unit tests with paired "accurate answer" and "hallucinated answer" scenarios.
- **Verification Criteria:**
  - Evaluator reliably flags answers claiming non-existent libraries or inverted logic as unsupported by repository evidence.
  - Accurate explanations receive high rubric scores and extract corroborating code line citations.

---

## Phase 5: Report Synthesis, Explanations & Retry Questions

- **Status:** *Not Started*
- **Objective:** Aggregate multi-turn evaluation data into a structured, readable performance report containing scores, strengths, weak topics, code-grounded explanations, and actionable retry questions.
- **Implementation Tasks:**
  - Define the report schema: overall score, per-topic breakdown, candidate quote highlights, code citations, weak topic analysis, conceptual explanations, and retry practice questions.
  - Implement report synthesis prompt in LangGraph's terminal node.
  - Add exporters for Markdown and JSON formats.
  - Persist report in the application SQLite database alongside interview session metadata.
- **Expected Deliverables:**
  - Module: `src/grillme/reporting/` (or `backend/app/reporting/`) containing report compilation, explanation generator, and formatting logic.
  - Sample generated report validating schema compliance and citation formatting.
- **Verification Criteria:**
  - Generated report contains all required sections (Summary, Topic Scores, Strengths, Weak Topics, Explanations, Retry Questions, Code Citations).
  - Scores are mathematically consistent with individual turn evaluations.

---

## Phase 6: Web Frontend & Interactive Chat Interface

- **Status:** *Not Started*
- **Objective:** Develop a clean, responsive web user interface using React + Vite + Tailwind CSS that allows candidates to submit repositories, view ingestion status, conduct the chat interview, and review their report.
- **Implementation Note:** *Developed in Phase 6 after the core backend interview flow (Phases 1–5) is verified and operational.*
- **Implementation Tasks:**
  - Set up React + Vite + Tailwind CSS frontend application.
  - Build Repository Submission view with input validation and loading spinners.
  - Build Ingestion Progress view displaying indexing status.
  - Build Interactive Chat view with message streaming, role tags, and turn indicators.
  - Build Post-Interview Report view with scorecards, explanations, retry questions, collapsible code snippets, and download options.
  - Connect frontend to FastAPI backend endpoints.
- **Expected Deliverables:**
  - Frontend codebase in `web/` or `frontend/`.
  - Working local web interface communicating smoothly with backend APIs.
- **Verification Criteria:**
  - A user can enter a URL, wait for ingestion, answer questions in chat, and view the rendered final report entirely in the browser.
  - UI gracefully displays backend loading states and error messages (e.g., repo not found).

---

## Phase 7: End-to-End Integration, Hardening & Local Deployment

- **Status:** *Not Started*
- **Objective:** Connect all components, harden error handling, prevent prompt injection, optimize performance, and provide a single-command local run experience.
- **Implementation Tasks:**
  - End-to-end integration tests covering the complete flow from URL input to final report export.
  - Implement prompt injection mitigations treating repository code and candidate answers as untrusted text.
  - Add request rate-limiting and input sanitization.
  - Create a single CLI startup script or `docker-compose.yml` for running backend and frontend locally.
  - Update user and developer documentation with step-by-step setup guides.
- **Expected Deliverables:**
  - End-to-end integration test suite in `tests/e2e/`.
  - Local run configuration and setup scripts.
  - Comprehensive documentation in `README.md`.
- **Verification Criteria:**
  - A developer can clone GrillMe, run a single setup command, and complete a full interview session locally.
  - End-to-end automated test passes cleanly in CI/test environments.

---

## Continuous Workstream: Evaluation, Benchmarking & Experiments

- **Status:** *Not Started*
- **Objective:** Maintain an empirical, reproducible discipline for evaluating retrieval quality and answer grading rigor—not just whether the application runs—using a manually verified benchmark.
- **Implementation Tasks:**
  - **Curate Manually Verified Benchmark:** Assemble a small, curated set of public reference repositories (Python and JavaScript/TypeScript).
  - **Ground-Truth Mapping:** Document known supporting code locations (files, functions, line ranges) and expected relevant chunks for benchmark queries.
  - **Paired Answer Dataset:** Create test sets of exemplary, partially correct, and intentionally hallucinated/incorrect answers with human-reviewed reference scores.
  - **Rubric Calibration:** Calibrate the fixed multi-dimensional rubric (Technical Accuracy, Implementation Depth, Architectural Clarity, Edge Case Awareness) against human evaluations to detect scoring drift.
  - **RAG & Chunking Experiments:** Run systematic experiments comparing:
    - Python and JS/TS structural chunking vs. fallback text chunking.
    - ChromaDB dense retrieval vs. hybrid BM25 + ChromaDB.
    - Embedding models and similarity thresholds.
  - Log all hypotheses, parameters, metrics, and conclusions in `EXPERIMENT_LOG.md`.
- **Expected Deliverables:**
  - Benchmark dataset and calibration evaluation scripts in `benchmarks/`.
  - Rigorous records of empirical findings in `EXPERIMENT_LOG.md`.
- **Verification Criteria:**
  - Automated benchmark suite evaluates both retrieval quality (Recall@k, MRR) and grading consistency against human reference scores.
  - Every architectural or algorithmic change to the RAG or evaluation pipeline is backed by logged experimental data demonstrating improvement.
