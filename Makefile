SHELL := /bin/bash
OLLAMA_URL ?= $(or $(DELEGATIONLAB_OLLAMA_URL),http://localhost:11434)

.PHONY: help install dev backend frontend check-ollama test lint format gen-api export static

help:
	@echo "make install   install backend (uv) and frontend (npm) dependencies"
	@echo "make dev       run backend :8000 + frontend :5173 (installs on first run)"
	@echo "make test      backend tests (excluding @ollama) + frontend typecheck"
	@echo "make lint      ruff, mypy, eslint"
	@echo "make format    auto-format backend code"
	@echo "make gen-api   regenerate frontend API types from the running backend"

# Stamp files so a clean clone installs automatically and later runs skip it.
backend/.venv/.installed: backend/pyproject.toml
	cd backend && uv sync
	@touch $@

frontend/node_modules/.installed: frontend/package.json frontend/package-lock.json
	cd frontend && npm ci
	@touch $@

install: backend/.venv/.installed frontend/node_modules/.installed

check-ollama:
	@if curl -sf --max-time 2 $(OLLAMA_URL)/api/version >/dev/null; then \
		echo "✓ Ollama reachable at $(OLLAMA_URL)"; \
	else \
		echo "⚠ Ollama not reachable at $(OLLAMA_URL); start it with 'ollama serve' (the dashboard will still run)"; \
	fi

dev: install check-ollama
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
