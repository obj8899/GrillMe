# GrillMe — AI Mock Interviewer for Your Own GitHub Projects

GrillMe is an AI-powered mock technical interviewer that analyzes a candidate's public GitHub repository, builds a repository-grounded knowledge base using RAG, and conducts an adaptive, evidence-based technical interview orchestrated by LangGraph.

---

## Current Status: Phase 0 Foundation

The project is currently at the foundation stage (**Phase 0**). The backend application skeleton and minimal health check endpoint are operational.

---

## Project Structure

```
d:\grillme\
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
│       │   └── config.py     # Pydantic Settings configuration
│       └── api/
│           ├── __init__.py
│           └── routes/
│               ├── __init__.py
│               └── health.py # Health check route (/health & /api/health)
└── tests/                    # Automated test suite
    ├── __init__.py
    ├── conftest.py           # TestClient fixtures
    └── test_health.py        # Health endpoint test suite
```

---

## Local Setup Guide (Windows 11 / PowerShell)

Follow these exact steps in PowerShell to set up and run GrillMe locally.

### 1. Prerequisites
- **Python 3.11+** installed and available in PATH.
- **Git** installed and configured.

Verify Python version:
```powershell
python --version
```
*(Expected: `Python 3.11.x` or newer)*

---

### 2. Virtual Environment Setup

From the project root directory (`D:\grillme`), create and activate a Python virtual environment:

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment in PowerShell
.\.venv\Scripts\Activate.ps1
```

> **Note on PowerShell Execution Policy:** If you encounter a script execution restriction, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

### 3. Install Dependencies

Install the core and development dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
```

---

### 4. Configure Environment Variables

Copy `.env.example` to create your local `.env`:

```powershell
Copy-Item .env.example .env
```

---

### 5. Run the Automated Tests

Execute the test suite using `pytest`:

```powershell
pytest
```

Expected output:
```
tests/test_health.py ... [100%]
3 passed in ...s
```

To run linting and code formatting checks:
```powershell
ruff check .
```

---

### 6. Start the Development Server

Start the FastAPI application using Uvicorn:

```powershell
uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

---

### 7. Access the Health Endpoint & API Documentation

Once the server is running, you can access the following endpoints in your browser or via curl/Invoke-RestMethod:

- **Root Info:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

#### Quick Verification via PowerShell:
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/health
```

Expected JSON response:
```json
{
  "status": "healthy",
  "service": "grillme-backend",
  "version": "0.1.0",
  "environment": "development"
}
```
