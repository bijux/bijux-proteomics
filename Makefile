# SPDX-License-Identifier: Apache-2.0
# Copyright © 2025 Bijan Mousavi

.DELETE_ON_ERROR:
.DEFAULT_GOAL := all
.SHELLFLAGS   := -eu -o pipefail -c
SHELL         := bash
PYTHON        := python3.11
RM            := rm -rf

.NOTPARALLEL: all clean

# ---- Single virtualenv (Python 3.11+) ----
VENV            := .venv
VENV_PYTHON     := $(if $(shell test -x "$(VENV)/bin/python" && echo yes),$(VENV)/bin/python,python3)
ACT             := $(if $(wildcard $(VENV)/bin/activate),$(VENV)/bin,)

# ---- Includes ----
include makefiles/test.mk
include makefiles/lint.mk
include makefiles/quality.mk
include makefiles/security.mk
include makefiles/build.mk
include makefiles/sbom.mk
include makefiles/docs.mk
include makefiles/api.mk
include makefiles/architecture.mk

-include .env
export

.PHONY: install ensure-venv nlenv \
        clean clean-soft clean-venv \
        manage_examples manage_models \
        all help

$(VENV):
	@echo "→ Creating virtualenv at '$(VENV)' with '$$(which $(PYTHON))' ..."
	@$(PYTHON) -m venv "$(VENV)"

ensure-venv: $(VENV) ## Ensure venv exists and deps are installed
	@set -e; \
	echo "→ Ensuring dependencies in $(VENV) ..."; \
	"$(VENV_PYTHON)" -m pip install --upgrade pip setuptools wheel; \
	EXTRAS="$${EXTRAS:-dev,local-esmfold}"; \
	if [ -n "$$EXTRAS" ]; then SPEC=".[$$EXTRAS]"; else SPEC="."; fi; \
	echo "→ Installing: $$SPEC"; \
	"$(VENV_PYTHON)" -m pip install -e "$$SPEC"

install: ensure-venv ## Install project into .venv (dev+nl+local-esmfold)
	@true

nlenv: ## Print activate command
	@echo "Run: source $(ACT)/activate"

clean-soft: ## Remove build artifacts but keep venv
	@echo "→ Cleaning (no .venv removal) ..."
	@$(RM) \
	  .pytest_cache htmlcov coverage.xml dist build *.egg-info .tox demo .tmp_home \
	  .ruff_cache .mypy_cache .pytype .hypothesis .coverage.* .coverage .benchmarks \
	  artifacts .cache || true
	@if [ "$(OS)" != "Windows_NT" ]; then \
	  find . -type d -name '__pycache__' -exec $(RM) {} +; \
	fi

clean-venv:
	@echo "→ Cleaning ($(VENV)) ..."
	@$(RM) "$(VENV)"

clean: clean-soft clean-venv ## Remove venv + artifacts

all: clean install test lint quality security sbom build docs api ## Full pipeline
	@echo "✔ All targets completed"

manage_examples:
	"$(VENV_PYTHON)" scripts/manage_examples.py

manage_models:
	"$(VENV_PYTHON)" scripts/manage_models.py

help: ## Show this help
	@awk 'BEGIN{FS=":.*##"; OFS="";} \
	  /^[a-zA-Z0-9_.-]+:.*##/ {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' \
	  $(MAKEFILE_LIST)
