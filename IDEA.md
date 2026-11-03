# GrillMe — Project Idea & Vision

## 1. Problem Statement

When software engineers and computer science students interview for technical roles, interviewers frequently focus on the candidates' personal or open-source projects listed on their resumes. Common interview questions include:
- *"Why did you choose this database over alternatives?"*
- *"Walk me through how data flows through this module."*
- *"What happens if this background worker crashes mid-task?"*
- *"How did you handle race conditions or authentication edge cases here?"*

Despite the importance of these questions, developers rarely practice defending their own code. Traditional interview preparation focuses almost exclusively on generic LeetCode-style data structures and algorithms or rehearsed behavioral STAR stories. Existing mock interview platforms have significant limitations:
- **Generic question banks:** Questions are disconnected from the candidate's actual design decisions and code.
- **No repository context:** Generic AI chatbots lack deep, structural understanding of a repository and cannot fact-check whether a candidate's verbal explanation matches what is actually in the code.
- **Superficial feedback:** Feedback lacks technical grounding because the evaluator cannot cross-reference the user's answers against repository facts.

Candidates enter technical interviews unprepared to articulate trade-offs, explain architecture, or acknowledge edge cases in their own code.

---

## 2. Project Vision

**GrillMe** is an AI-powered mock interviewer tailored specifically to a developer's own GitHub projects. 

A user provides a public GitHub repository link. GrillMe digests the codebase, builds a repository-grounded knowledge base, and conducts an adaptive, multi-turn technical interview. GrillMe acts as a senior engineer or hiring manager who has reviewed the candidate's repository in detail:
- Asking high-level architectural questions.
- Drilling into specific files, classes, and design decisions.
- Probing edge cases, scalability bottlenecks, and failure modes.
- Verifying the candidate's answers against the actual codebase using Retrieval-Augmented Generation (RAG).
- Providing an objective, evidence-based post-interview evaluation report with scores, identified weak topics, grounded explanations, and retry questions.

GrillMe bridges the gap between writing code and defending it in real-world technical discussions.

---

## 3. Target Users

1. **CS Students & New Graduates:** Preparing for entry-level and junior software engineering roles where capstone or portfolio projects are the primary demonstration of skill.
2. **Self-Taught & Bootcamp Developers:** Looking to prove technical depth and show that their projects are not just copy-pasted tutorials, but well-understood systems.
3. **Experienced Engineers:** Refreshing their memory on past personal or open-source projects before major job interviews.
4. **Mentors, Educators & Career Coaches:** Seeking a structured, reproducible tool to help students practice technical project defenses.

---

## 4. Core Features

### A. Repository Ingestion & Analysis
- Clones and inspects public GitHub repositories safely without executing repository code.
- Parses directory trees, dependency files, documentation (`README.md`, docs), and source code files.
- Filters out non-essential assets, compiled binaries, vendor directories, and lockfiles to focus strictly on business logic and architecture.

### B. Codebase Knowledge Base & RAG
- Indexes project files using syntax-aware structural chunking (initial support for Python and JavaScript/TypeScript) and extensible fallback text chunking for documentation and other languages.
- Uses ChromaDB as the sole initial local vector store behind a minimal abstraction interface.
- Combines semantic vector search with keyword/symbol search (hybrid retrieval) to locate exact references (e.g., function names, API routes, configurations).

### C. Adaptive Technical Interviewing (LangGraph)
- Orchestrates multi-turn interview conversations with a defined state machine.
- Paces the interview through logical phases: high-level architecture overview, module deep-dives, failure-mode challenges, and technical trade-off discussions.
- Manages human-in-the-loop pauses after asking a question and resumes seamlessly upon receiving the candidate's answer via SQLite-backed checkpointing.
- Dynamically adapts follow-up questions based on the candidate's responses (probing vague answers, moving forward on solid explanations).

### D. Evidence-Based Answer Fact-Checking
- Cross-references candidate claims against retrieved code snippets.
- Detects hallucinations, hand-waving, or inaccurate claims (e.g., a candidate claiming *"We used Redis caching"* when the repository contains no cache layer).

### E. Comprehensive Performance Report & Feedback
- Generates a post-interview evaluation across multiple dimensions:
  - System Architecture & High-Level Understanding
  - Implementation Accuracy & Code Familiarity
  - Edge Case & Error Handling Awareness
  - Trade-off Justification & Alternative Design Thinking
- Delivers actionable feedback:
  - Dimension scores and topic breakdowns.
  - Specific candidate quotes with matching code citations.
  - Identification of weak topics and technical inaccuracies.
  - Clear explanations of the underlying code architecture.
  - Targeted follow-up and retry questions for continued practice.

---

## 5. User Journey

```
[1. User Submits Repo URL]
        │
        ▼
[2. GrillMe Ingests & Indexes Codebase]
        │
        ▼
[3. System Generates Project Overview & Interview Plan]
        │
        ▼
[4. Multi-Turn Interactive Chat Interview (Pause/Resume Graph)]
    ├── AI asks architecture/code question (Graph Pauses & Checkpoints)
    ├── User submits explanation via API
    ├── Graph resumes, retrieves repository evidence & validates claim
    └── AI asks adaptive follow-up or advances topic
        │
        ▼
[5. Interview Wrap-up & Scoring]
        │
        ▼
[6. Structured Performance Report, Explanations & Retry Questions]
```

1. **Submission:** The user pastes a public GitHub repository URL into the GrillMe interface and selects optional interview parameters (e.g., focus area: Architecture vs. Implementation; difficulty/seniority level).
2. **Analysis:** GrillMe clones the repository, parses the file hierarchy and key files, builds vector embeddings in ChromaDB, and initializes an interview topic outline.
3. **The Grilling Session:**
   - The AI interviewer begins by asking the user to explain the overarching architecture and primary user flow. The graph pauses and checkpoints state.
   - The user submits their answer. The graph resumes, retrieves verifying evidence, and grades the response.
   - Based on the user's response, the AI transitions to component-level questions (e.g., *"In `auth_service.py`, how are expired tokens invalidated?"*).
   - If the user provides a strong answer, the AI escalates to edge cases or trade-offs (*"Why did you choose polling over WebSockets for updates?"*).
   - If the user provides an inaccurate or vague answer, the AI probes deeper (*"You mentioned using a message queue, but I only see synchronous HTTP endpoints in the repo. Where is that handled?"*).
4. **Debrief:** Once the interview reaches the configured turn limit or covers planned topics, the session concludes.
5. **Report:** The user receives a detailed report identifying strong answers, weak topics, fact-check discrepancies, explanations of the actual codebase logic, and retry questions to reinforce learning.

---

## 6. v1 Scope and Exclusions

To ensure a focused, reliable, and high-quality initial release, the scope for version 1 is strictly delineated.

### In Scope for v1:
- **Public GitHub repositories first:** Accessed via standard public clone or public GitHub APIs without requiring user credentials.
- **Text-based chat interface:** Single-window multi-turn conversational interview.
- **Single repository per interview:** Multi-repo or distributed cross-repo setups are treated as separate sessions.
- **Repository size constraints:** Practical limits on repository size (e.g., max total file size or maximum number of code files) to maintain fast ingestion and control indexing costs.
- **Initial language parsing scope:** Syntax-aware structural chunking for **Python** and **JavaScript/TypeScript**, with an extensible parser interface and a fallback sliding-window text chunker for documentation and unsupported languages.
- **ChromaDB as sole local vector store:** Accessed via a minimal `VectorStore` abstraction interface.
- **RAG-based evidence retrieval:** Semantic and keyword retrieval over indexed code.
- **LangGraph orchestration:** Stateful interview flow with SQLite-backed checkpointing for turn-based pause/resume.
- **Automated post-interview report:** Objective evaluation scorecard, weak topic analysis, code explanations, and retry questions.

### Out of Scope for v1 (Future Iterations):
- **Private repositories:** No GitHub OAuth integration or personal access token handling in v1 (planned for a later extension).
- **Execution of repository code:** GrillMe never runs, builds, or executes code from ingested repositories.
- **Resume-based personalization:** Tailoring questions to candidate resumes is deferred to a future iteration and is not a blocker for the first working system.
- **Voice or video interviews:** No real-time audio/speech-to-text (STT) or text-to-speech (TTS) streaming.
- **Live coding & sandboxed execution:** No in-browser code editor, terminal runner, or test suite execution.
- **Autonomous code modification:** GrillMe will *never* write pull requests, edit files, or commit code to the repository.
- **Monorepo multi-service profiling:** Extremely large repositories (e.g., Linux kernel, Chromium) will not be supported in initial ingestion pipelines.
- **User authentication & payment systems:** Local/single-user development focus before multi-tenant cloud hosting.

---

## 7. Expected Outcomes

- **Realistic Interview Practice:** Candidates experience authentic technical questioning grounded in real code they wrote.
- **Objective Self-Assessment:** Candidates discover blind spots in their own projects before a real hiring manager finds them.
- **Actionable Learning:** Post-interview reports provide scores, weak topics, grounded explanations of code patterns, and concrete retry questions.
- **Reproducible Evaluation:** Clear grading rubrics calibrated against manually verified benchmarks ensure consistent, drift-free feedback across interview sessions.
