.PHONY: help venv install setup install-deps lint lint-fix format format-check typecheck test security snyk checks fix

VENV ?= .venv
PYTHON := $(VENV)/bin/python
UV := uv

help:
	@echo "Targets:"
	@echo "  setup          - create/update venv and install dependencies"
	@echo "  venv           - create or update virtual environment at $(VENV)"
	@echo "  install        - install project + dev dependencies into $(VENV)"
	@echo "  lint           - ruff check (lint)"
	@echo "  lint-fix       - ruff check --fix"
	@echo "  format         - ruff format (apply)"
	@echo "  format-check   - ruff format --check"
	@echo "  typecheck      - mypy"
	@echo "  test           - pytest"
	@echo "  security       - bandit scan"
	@echo "  snyk           - run snyk test (requires snyk CLI and SNYK_TOKEN)"
	@echo "  checks         - run lint, format-check, typecheck, test, security"
	@echo "  fix            - run format + lint-fix"

setup: venv install

venv:
	$(UV) venv $(VENV)

install:
	$(UV) pip install --python $(PYTHON) -e .[dev]

lint:
	$(UV) run ruff check .

lint-fix:
	$(UV) run ruff check --fix .

format:
	$(UV) run ruff format .

format-check:
	$(UV) run ruff format --check .

typecheck:
	$(UV) run mypy .

test:
	$(UV) run pytest

security:
	$(UV) run bandit -q -r src

checks: lint format-check typecheck test security

fix: format lint-fix
