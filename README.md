# DelegationLab

A local research platform for running simulated delegation elicitation experiments with LLM-driven personas. Personas answer a self-report survey and play a delegation game, and the engine scores how much of each persona's hidden delegation policy each instrument recovers.

Everything runs on your machine: a FastAPI backend at `localhost:8000`, a React dashboard at `localhost:5173`, and Ollama at `localhost:11434`.

**Status:** milestone M1 (LLM gateway). The backend serves `/api/health`, `/api/models` and the model benchmark. The dashboard shell still has empty pages; they are filled in later milestones.

## Prerequisites

- [uv](https://docs.astral.sh/uv/): `curl -LsSf https://astral.sh/uv/install.sh | sh`, then open a new Terminal window. It installs Python 3.12 automatically.
- Node.js 20+ and npm: `brew install node`.
- [Ollama](https://ollama.com), with a model pulled: `ollama pull gemma3:12b` (see [Hardware](#hardware)).

`make doctor` checks these and prints the install command for anything missing.

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
| `make doctor` | check that uv, node, npm and curl are installed |
| `make benchmark MODEL=gemma3:12b` | benchmark a model: 10 fixed calls, stores mean/p95 latency, tokens/s and JSON validity rate (backend must be running) |
| `make test-ollama MODEL=gemma3:12b` | one real structured call against your local Ollama (skips if Ollama or the model is missing) |
| `make gen-api` | regenerate `frontend/src/lib/api-types.ts` from the running backend's OpenAPI spec |

Configuration comes from environment variables with the `DELEGATIONLAB_` prefix, or from a `.env` file at the repo root. See `.env.example`. Runtime data (the SQLite database, call logs and exports) is written to `data/`, which is gitignored.

## Hardware

The engine never assumes a speed. `make benchmark` measures it on your machine, and run-time estimates are built from that measurement.

| Mac memory | Default model | Parallel slots | Notes |
|---|---|---|---|
| 8 GB | `gemma3:4b` | 1 | Fine for development; persona play is weaker |
| **16 GB** (current target: M3 MacBook Air) | **`gemma3:12b`** | **2** | ~8 GB of weights. Leaves room for macOS, the browser and the dev servers |
| 24 GB | `gemma3:12b` | 2–3 | `qwen3:14b` is also an option |
| 64 GB | `gemma3:27b` | 4 | The PRD's original target; ~17 GB of weights |

`gemma3:4b` is also useful on any machine for fast pipeline checks. Set the default with `DELEGATIONLAB_DEFAULT_MODEL` and the concurrency with `DELEGATIONLAB_DEFAULT_CONCURRENCY` (see `.env.example`).

The MacBook Air has no fan. On long runs it slows down as it heats up, so re-benchmark after a long run if estimates drift.

### Ollama settings (macOS)

```bash
launchctl setenv OLLAMA_NUM_PARALLEL 2
launchctl setenv OLLAMA_KEEP_ALIVE 30m
```

Then quit and reopen the Ollama app. `OLLAMA_NUM_PARALLEL` must be at least the configured concurrency for calls to run in parallel. `OLLAMA_KEEP_ALIVE` keeps the model loaded between calls.

## Troubleshooting

- **`Port 8000 is already in use`**: an earlier `make dev`, or another app, is still running. `make dev` names the process. Stop it with `make stop`, then run `make dev` again.
- **`uv: command not found`** right after installing uv: open a new Terminal window so your shell finds `~/.local/bin`.
- **"accepts 1 arg(s), received N"** or similar: the macOS Terminal (zsh) does not treat `# ...` after a command as a comment. Paste commands without trailing comments.

## Reproducibility

Every LLM call gets a seed derived from the run seed, task and retry index. Every call is logged in full to `data/runs/<run_id>/calls.jsonl` (benchmarks: `data/benchmarks/<id>/calls.jsonl`) and indexed in SQLite.

Ollama is not bit-for-bit reproducible when it serves parallel requests, even with fixed seeds. The response cache is the reproducibility guarantee: rerunning the same experiment with the same seed and a warm cache returns identical results.

## Deviations from the PRD

- Target machine is a 16 GB M3 MacBook Air rather than a 64 GB M5 Pro, so the default model is `gemma3:12b` (not `gemma3:27b`) and default concurrency is 2 (not 4). M1's acceptance check is therefore "benchmarking `gemma3:12b` stores latency, tokens/s, validity rate".

## Layout

```
backend/        FastAPI app (delegationlab/), tests/
frontend/       Vite + React + TypeScript dashboard
prompts/        Jinja2 prompt templates, one folder per module (benchmark/ ships now)
schemas/        delegation and scenario feature schemas
library/        scenario and persona libraries
experiments/    saved experiment configs
data/           runtime data (gitignored)
static-viewer/  read-only results viewer build target
```
