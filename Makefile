SHELL := /bin/bash
OLLAMA_URL ?= $(or $(DELEGATIONLAB_OLLAMA_URL),http://localhost:11434)

MODEL ?= gemma3:12b
PROVIDER ?= ollama

DEV_PORTS := 8000 5173

.PHONY: help doctor install dev stop backend frontend check-ollama check-ports test test-ollama \
	lint format gen-api \
	benchmark export static

help:
	@echo "make doctor    check that uv, node, npm and curl are installed"
	@echo "make install   install backend (uv) and frontend (npm) dependencies"
	@echo "make dev       run backend :8000 + frontend :5173 (installs on first run)"
	@echo "make stop      stop whatever is listening on ports 8000 and 5173"
	@echo "make test      backend tests (excluding @ollama) + frontend typecheck"
	@echo "make lint      ruff, mypy, eslint"
	@echo "make format    auto-format backend code"
	@echo "make gen-api   regenerate frontend API types from the running backend"
	@echo "make benchmark MODEL=gemma3:12b   benchmark a model (backend must be running)"
	@echo "make test-ollama                  one real call against local Ollama"

doctor:
	@missing=0; \
	command -v uv >/dev/null || { missing=1; echo "✗ uv is not installed. Run:"; \
		echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"; \
		echo "  then open a new Terminal window."; }; \
	command -v node >/dev/null && command -v npm >/dev/null || { missing=1; \
		echo "✗ Node.js is not installed. Run:  brew install node   (or get it from nodejs.org)"; }; \
	command -v curl >/dev/null || { missing=1; echo "✗ curl is not installed."; }; \
	if [ $$missing = 1 ]; then exit 1; fi; \
	echo "✓ uv, node, npm and curl found"

# Stamp files so a clean clone installs automatically and later runs skip it.
backend/.venv/.installed: backend/pyproject.toml | doctor
	cd backend && uv sync
	@touch $@

frontend/node_modules/.installed: frontend/package.json frontend/package-lock.json | doctor
	cd frontend && npm ci
	@touch $@

install: backend/.venv/.installed frontend/node_modules/.installed

check-ollama:
	@if curl -sf --max-time 2 $(OLLAMA_URL)/api/version >/dev/null; then \
		echo "✓ Ollama reachable at $(OLLAMA_URL)"; \
	else \
		echo "⚠ Ollama not reachable at $(OLLAMA_URL); start it with 'ollama serve' (the dashboard will still run)"; \
	fi

# Refuse to start when a port is taken (e.g. a backend left over from an earlier `make dev`),
# instead of letting one server die while the other keeps running.
check-ports:
	@if ! command -v lsof >/dev/null; then echo "(lsof not found; skipping port check)"; exit 0; fi; \
	busy=0; \
	for port in $(DEV_PORTS); do \
		pids=$$(lsof -nP -iTCP:$$port -sTCP:LISTEN -t 2>/dev/null); \
		if [ -n "$$pids" ]; then \
			busy=1; \
			echo "✗ Port $$port is already in use by:"; \
			for pid in $$pids; do echo "    $$(ps -o pid=,command= -p $$pid)"; done; \
			echo "  Stop it with:  kill $$(echo $$pids)"; \
		fi; \
	done; \
	if [ $$busy = 1 ]; then echo "  Or stop both ports at once with:  make stop"; exit 1; fi

stop:
	@if ! command -v lsof >/dev/null; then echo "lsof not found; cannot look up processes"; exit 1; fi; \
	for port in $(DEV_PORTS); do \
		pids=$$(lsof -nP -iTCP:$$port -sTCP:LISTEN -t 2>/dev/null); \
		if [ -n "$$pids" ]; then \
			kill $$pids && echo "Stopped process $$(echo $$pids) on port $$port"; \
		else \
			echo "Port $$port is free"; \
		fi; \
	done

dev: install check-ports check-ollama
	@trap 'kill 0' EXIT INT TERM; \
	(cd backend && uv run uvicorn delegationlab.main:create_app --factory --reload --port 8000) & \
	(cd frontend && npm run dev) & \
	wait

backend: backend/.venv/.installed
	cd backend && uv run uvicorn delegationlab.main:create_app --factory --reload --port 8000

frontend: frontend/node_modules/.installed
	cd frontend && npm run dev

test: install
	cd backend && uv run pytest
	cd frontend && npm run typecheck

test-ollama: backend/.venv/.installed
	cd backend && DELEGATIONLAB_TEST_MODEL=$(MODEL) uv run pytest -m ollama -o addopts="" -v

benchmark:
	@curl -sf -X POST "http://localhost:8000/api/models/$(MODEL)/benchmark?provider=$(PROVIDER)" \
		| python3 -m json.tool \
		|| echo "Benchmark failed: is the backend running (make dev) and is $(MODEL) pulled?"

lint: install
	cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy delegationlab
	cd frontend && npm run lint

format: backend/.venv/.installed
	cd backend && uv run ruff format . && uv run ruff check --fix .

gen-api: frontend/node_modules/.installed
	cd frontend && npm run gen:api

export:
	@echo "make export RUN=<id> is available from milestone M7"; exit 1

static:
	@echo "make static RUN=<id> is available from milestone M7"; exit 1
