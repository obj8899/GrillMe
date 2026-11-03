# GrillMe — Architecture Decision Records (ADRs)

This document tracks significant architectural and technical decisions made for **GrillMe**. Each record captures the context, chosen direction, status, and associated trade-offs.

---

## ADR Template for Future Decisions

When adding a new architectural decision, copy the template below and assign the next sequential ID:

```markdown
### ADR-XXX: [Short, descriptive title]

- **Status:** Proposed | Accepted | Deprecated | Superseded
- **Date:** YYYY-MM-DD
- **Author(s):** [Name / Agent]

#### Context & Problem Statement
What is the problem being addressed? What constraints or requirements motivate this decision?

#### Considered Options
1. Option A: ...
2. Option B: ...

#### Decision & Rationale
What was chosen and why? How does it satisfy the project goals?

#### Consequences & Trade-offs
- **Positive:** Benefits gained.
- **Negative / Risks:** Trade-offs, limitations, or additional complexity introduced.
- **Mitigation:** How negative consequences will be handled.
```

---

## Active & Proposed Decisions

### ADR-001: Adoption of Retrieval-Augmented Generation (RAG) for Codebase Grounding

- **Status:** Proposed
- **Date:** 2026-11-03
- **Author(s):** Core Team

#### Context & Problem Statement
To conduct an effective interview on a developer's repository, the AI interviewer needs precise awareness of the code, architecture, and configuration. While modern LLMs have growing context windows, stuffing an entire multi-thousand-line repository into a prompt on every turn is cost-prohibitive, introduces high latency, and degrades reasoning precision (the "needle-in-a-haystack" problem).

#### Considered Options
1. **Full-Context Ingestion:** Paste the entire repository text into the prompt context for every turn.
2. **Abstract-Only Profiling:** Generate a high-level summary at ingestion and rely solely on the summary without referring back to code.
3. **Retrieval-Augmented Generation (RAG):** Index chunked repository files and dynamically retrieve relevant classes, functions, and configs based on the conversation turn and candidate claims.

#### Decision & Rationale
Adopt **Retrieval-Augmented Generation (RAG)** using structural/syntax-aware chunking combined with hybrid (dense vector + sparse keyword) retrieval. RAG allows GrillMe to ground questions and fact-check candidate claims against exact file locations and code snippets while keeping token consumption and latency manageable.

#### Consequences & Trade-offs
- **Positive:** Scales to medium and large codebases; keeps token costs low; enables precise fact-checking by providing exact file and line references.
- **Negative / Risks:** Code chunking is harder than plain text chunking; poor chunking can sever dependencies and destroy context; requires embedding and vector store infrastructure.
- **Mitigation:** Use structural chunking (preserving class/function boundaries) and hybrid search (BM25 + embeddings) to preserve precision.

---

### ADR-002: Using LangGraph for Interview Orchestration

- **Status:** Proposed
- **Date:** 2026-11-03
- **Author(s):** Core Team

#### Context & Problem Statement
A technical interview is not a simple question-and-answer loop. It requires structured pacing: an initial greeting and system overview, followed by deep dives into selected modules, adaptive follow-up probing when answers are weak or contradictory, and a final debrief with scoring. An unstructured single-prompt chatbot cannot reliably enforce this flow without losing track of interview progress.

#### Considered Options
1. **Unstructured Prompt Chaining:** Single multi-turn LLM chat thread relying on system prompt instructions to manage pacing.
2. **Hardcoded Procedural Script (Python state loop):** Pure Python code managing state transitions with LLM calls embedded as plain functions.
3. **LangGraph State Graph:** A stateful, graph-based workflow engine providing cyclic transitions, state checkpointing, and conditional routing.

#### Decision & Rationale
Adopt **LangGraph** for orchestrating the interview workflow. LangGraph provides explicit state schemas, checkpointing, cyclic graphs (essential for retry/probing loops), and conditional routing based on candidate answer evaluations.

#### Consequences & Trade-offs
- **Positive:** Deterministic control over interview stages; clear separation of nodes (question generation, fact-checking, scoring, report generation); built-in state persistence.
- **Negative / Risks:** Adds a framework dependency; requires learning curve for graph schemas and state management.
- **Mitigation:** Keep the state schema clean, typed, and well-documented with minimal node complexity.

---

### ADR-003: Public GitHub Repositories Only for Initial Scope (v1)

- **Status:** Proposed
- **Date:** 2026-11-03
- **Author(s):** Core Team

#### Context & Problem Statement
Supporting private repositories requires GitHub OAuth app registration, handling user credentials, managing sensitive token lifecycles, and assuming legal/security risks for private source code.

#### Considered Options
1. **Full GitHub OAuth & Private Repo Access in v1:** Request user permissions and read private repositories immediately.
2. **Public GitHub Repositories First:** Support only publicly accessible repositories in v1, deferring OAuth and private repo access to a subsequent release.

#### Decision & Rationale
Limit version 1 strictly to **public GitHub repositories**. Anyone can test and use the application without authentication setup, eliminating credential storage vulnerabilities and simplifying early development.

#### Consequences & Trade-offs
- **Positive:** Zero credential handling overhead; low security attack surface; faster path to a working prototype.
- **Negative / Risks:** Users with closed-source or private portfolio projects cannot test them without making them public.
- **Mitigation:** Design the ingestion interface as an abstract fetcher so a future authenticated private repository fetcher can be dropped in cleanly.

---

### ADR-004: Modular Separation of Concerns

- **Status:** Proposed
- **Date:** 2026-11-03
- **Author(s):** Core Team

#### Context & Problem Statement
Building an AI system where API routing, ingestion, vector search, orchestration, and evaluation are intertwined makes testing, debugging, and iterative learning difficult.

#### Considered Options
1. **Monolithic Script / Flat Architecture:** Implement everything in a few large backend scripts.
2. **Decoupled Modular Architecture:** Separate functional domains into independent packages: `ingestion`, `rag`, `orchestrator`, `evaluation`, `reporting`, and `api`.

#### Decision & Rationale
Enforce a **strictly decoupled modular architecture**. Each package has a single responsibility, well-defined typed interfaces, and independent unit tests.

#### Consequences & Trade-offs
- **Positive:** Easy to unit-test components in isolation; clean mental model for students and new contributors; components can be upgraded without breaking others.
- **Negative / Risks:** Slightly more boilerplate and interface definition work up front.
- **Mitigation:** Maintain clear type definitions and docstrings in each module.

---

### ADR-005: Static Code Analysis vs. Dynamic Runtime Execution

- **Status:** Proposed
- **Date:** 2026-11-03
- **Author(s):** Core Team

#### Context & Problem Statement
An interviewer could theoretically evaluate a candidate's project by running its test suite, building containers, or profiling live performance. However, executing arbitrary user code poses major security and infrastructure challenges.

#### Considered Options
1. **Dynamic Sandbox Execution:** Build and run repository code in secure Docker containers to verify test suites and runtime metrics.
2. **Static Code Analysis & RAG:** Inspect code files, configuration, tests, and documentation purely through static parsing and text retrieval without executing the code.

#### Decision & Rationale
Adopt **Static Code Analysis & RAG** for v1. GrillMe's core mission is to interview the human candidate on their design rationale, architecture, and edge cases, not to act as a CI runner. Static analysis is safe, fast, inexpensive, and eliminates the risk of running untrusted code.

#### Consequences & Trade-offs
- **Positive:** No container isolation risks; no complex environment setup (missing databases, secrets, external APIs); instant analysis.
- **Negative / Risks:** Cannot verify runtime performance, benchmarks, or if the code actually compiles/runs cleanly.
- **Mitigation:** The AI interviewer can specifically ask the candidate about build steps, testing strategies, and runtime performance during the interview.

---

### ADR-006: ChromaDB as Sole Initial Local Vector Store via Abstraction

- **Status:** Proposed
- **Date:** 2026-11-03
- **Author(s):** Core Team

#### Context & Problem Statement
Vector retrieval requires an indexing and search engine. Supporting multiple vector database backends during early development adds maintenance overhead and configuration bloat, while cloud-hosted options (Pinecone, Weaviate Cloud) require external accounts and API keys.

#### Considered Options
1. **Cloud Vector Service (e.g., Pinecone):** High scalability but requires network access and external API credentials.
2. **Multiple Vector Databases in v1 (ChromaDB + Qdrant):** Premature multi-store complexity before core interview flows are verified.
3. **ChromaDB Exclusively for v1 behind a Minimal Abstraction:** An embedded vector database running locally in-process, accessed strictly through a minimal `VectorStore` interface.

#### Decision & Rationale
Adopt **ChromaDB as the sole initial local vector store for v1**, accessed strictly via a clean, minimal `VectorStore` abstraction interface. ChromaDB runs embedded locally with zero external cloud accounts. Defining a clean abstraction prevents vendor lock-in and allows dropping in alternative stores in future versions without rewriting retrieval or orchestration logic. Do not implement Qdrant or other vector store implementations in v1.

#### Consequences & Trade-offs
- **Positive:** Zero external setup; runs completely offline/locally; zero cloud costs; clean interface boundaries for future extension.
- **Negative / Risks:** Limited multi-tenant scaling on massive indexes compared to dedicated distributed clusters.
- **Mitigation:** The `VectorStore` interface guarantees that switching to a production-grade store later requires only a single new adapter class.

---

### ADR-007: SQLite-Backed Persistence for LangGraph State Checkpointing

- **Status:** Proposed
- **Date:** 2026-11-03
- **Author(s):** Core Team

#### Context & Problem Statement
LangGraph orchestrates multi-turn technical interviews where the graph must pause after generating a question, await candidate input over HTTP, and resume execution. If the backend process recycles or restarts between turns, in-memory state is permanently lost, stranding the interview.

#### Considered Options
1. **In-Memory Checkpointing (`MemorySaver`):** Simple and built-in, but state vanishes on server restart or process recycle.
2. **SQLite-Backed Checkpointing:** Lightweight, persistent local file storage that preserves graph execution checkpoints across server restarts with zero external infrastructure.
3. **External Distributed Database (e.g., PostgreSQL / Redis):** Robust for high concurrency but introduces external infrastructure overhead and local setup friction for students and developers.

#### Decision & Rationale
Adopt **SQLite-backed persistence as the primary checkpointer** for LangGraph graph state in local development.
- SQLite checkpoints persist graph state across HTTP turns and server restarts.
- Reserve `MemorySaver` solely for small, isolated unit test experiments.
- **Implementation Caveat:** The implementation must use the appropriate LangGraph checkpointer package and API for the installed version (e.g., verify whether the installed version provides `SqliteSaver` in `langgraph.checkpoint.sqlite` or a companion package, rather than assuming an API name without verification during implementation).
- **Separation of Concerns:** LangGraph graph checkpoints and relational application session data (e.g., user profiles, session metadata, transcripts, final report records) have distinct responsibilities and schemas, even though SQLite is used for both.

#### Consequences & Trade-offs
- **Positive:** In-progress interviews survive process recycles and restarts; zero cloud dependencies; clean state resumption.
- **Negative / Risks:** Potential SQLite write locking under high concurrent load; requires checking exact package/API names during Phase 3 implementation.
- **Mitigation:** Concurrency is low for single-user local development; package imports will be tested and verified directly during Phase 3 setup.
