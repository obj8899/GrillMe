# GrillMe — ML & RAG Experiment Log

This document records empirical experiments conducted to evaluate and improve GrillMe's retrieval-augmented generation (RAG) pipeline, chunking strategies, prompt engineering, and answer evaluation accuracy.

> **Instruction:** Do not fabricate experiment results. Only record actual experiments after running benchmarks against curated test repositories.

---

## Experiment Entry Template

Copy and paste the template below to log an experiment:

```markdown
### EXP-XXX: [Descriptive Experiment Title]

- **Date:** YYYY-MM-DD
- **Author:** [Name / Agent]
- **Status:** Planned | In Progress | Completed | Abandoned

#### 1. Hypothesis
What specific change are you testing, and what improvement do you expect?
*(Example: "Using AST-based structural chunking instead of 500-token fixed chunking will increase Recall@3 on symbol retrieval from 65% to 85%.")*

#### 2. Dataset / Test Repositories
What codebase(s) and query benchmark are being used for testing?
- **Repository:** [e.g., `owner/repo-name` at commit `hash`]
- **Language / Domain:** [e.g., Python / FastAPI microservice]
- **Benchmark Set:** [e.g., 20 ground-truth questions and expected code file/line references]

#### 3. Method & Configuration
Document the exact parameters and techniques tested:
- **Chunking Strategy:** [e.g., AST-based vs. Fixed-size token window (500 tokens / 50 overlap)]
- **Embedding Model:** [e.g., text-embedding-3-small, text-embedding-004, etc.]
- **Retriever:** [e.g., Dense vector only vs. Hybrid BM25 + Dense RRF]
- **Prompt Template:** [Reference to prompt version or parameters]
- **LLM Evaluator:** [Model used for evaluation, e.g., gpt-4o, claude-3-5-sonnet, gemini-1.5-pro]

#### 4. Evaluation Metrics
Define how performance is measured:
- **Retrieval Precision / Recall:** (e.g., Recall@k, Mean Reciprocal Rank - MRR)
- **Answer Faithfulness / Groundedness Score:** (1 to 5 scale or percentage of claims verified by code)
- **Evaluation Agreement:** (Alignment between human grading and LLM evaluator)
- **Latency / Cost:** (Average response time in seconds, token usage per turn)

#### 5. Results
Summarize quantitative and qualitative observations:

| Metric | Baseline | Experimental Variant | Delta / Impact |
|---|---|---|---|
| Recall@3 | — | — | — |
| Faithfulness Score | — | — | — |
| Retrieval Latency | — | — | — |

*Qualitative Observations:*
- [Observation 1]
- [Observation 2]

#### 6. Interpretation & Analysis
- Did the data support the hypothesis? Why or why not?
- What unexpected failures or edge cases were discovered?

#### 7. Next Steps & Decisions Taken
- [ ] [Action item 1: e.g., Adopt experimental variant as default in `DECISIONS.md`]
- [ ] [Action item 2: e.g., Run follow-up experiment testing different embedding models]
```

---

## Experiment Registry

| ID | Date | Title | Focus Area | Status | Key Outcome |
|---|---|---|---|---|---|
| *EXP-001* | *Planned* | *AST Chunking vs. Fixed-Token Chunking on Python Repos* | *RAG Chunking* | *Planned* | *Pending Phase 2 setup* |

*(No experiments have been run yet. Results will be logged once Phase 2 benchmarking begins.)*

