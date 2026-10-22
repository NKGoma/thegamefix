# DelegationLab

A local research platform for running simulated delegation elicitation experiments with LLM-driven personas. Personas answer a self-report survey and play a delegation game, and the engine scores how much of each persona's hidden delegation policy each instrument recovers.

Everything runs on your machine: a FastAPI backend at `localhost:8000`, a React dashboard at `localhost:5173`, and Ollama at `localhost:11434`.

**Status:** milestone M0 (scaffold). The backend serves `/api/health` and the dashboard shell has empty pages. See the PRD for the milestone plan.

## Prerequisites

- [uv](https://docs.astral.sh/uv/). It installs Python 3.12 automatically if needed.
- Node.js 20+ and npm.
- [Ollama](https://ollama.com) (optional for M0). Pull the default model with `ollama pull gemma3:27b`.

## Quick start

```bash
make dev
```

On a fresh clone this installs the dependencies, checks whether Ollama is reachable, and starts both servers. Open http://localhost:5173. The status pill at the bottom of the sidebar is green when Ollama responds.

| Command | What it does |
|---|---|
| `make dev` | backend (auto-reload) and frontend dev server |
| `make test` | backend tests (excluding `@pytest.mark.ollama`) and frontend type check |
| `make lint` | ruff, mypy (strict on `engine/`), eslint |
| `make gen-api` | regenerate `frontend/src/lib/api-types.ts` from the running backend's OpenAPI spec |

Configuration comes from environment variables with the `DELEGATIONLAB_` prefix, or from a `.env` file at the repo root. See `.env.example`. Runtime data (the SQLite database, call logs and exports) is written to `data/`, which is gitignored.

## Recommended Ollama settings (macOS)

```bash
launchctl setenv OLLAMA_NUM_PARALLEL 4     # must be >= llm.max_concurrency for real parallelism
launchctl setenv OLLAMA_KEEP_ALIVE 30m
# then restart the Ollama app
```

## Layout

```
backend/        FastAPI app (delegationlab/), tests/
frontend/       Vite + React + TypeScript dashboard
prompts/        Jinja2 prompt templates, one folder per module
schemas/        delegation and scenario feature schemas
library/        scenario and persona libraries
experiments/    saved experiment configs
data/           runtime data (gitignored)
static-viewer/  read-only results viewer build target
```
