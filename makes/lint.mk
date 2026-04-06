# Lint Configuration (no root cache pollution)

VENV_PYTHON ?= python3
RUFF        ?= $(VENV_PYTHON) -m ruff
MYPY        ?= $(VENV_PYTHON) -m mypy
CODESPELL   ?= $(if $(ACT),$(ACT)/codespell,codespell)
PYDOCSTYLE  ?= $(VENV_PYTHON) -m pydocstyle
RADON       ?= $(VENV_PYTHON) -m radon

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/util.mk

LINT_SCOPE             ?=
LINT_DIRS              ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab
FMT_DIRS               ?= $(if $(LINT_SCOPE),$(LINT_SCOPE),$(LINT_DIRS))
LINT_TARGETS           ?= $(if $(LINT_SCOPE),$(LINT_SCOPE),$(LINT_DIRS))
MYPY_TARGETS           ?= $(LINT_TARGETS)
CODESPELL_TARGETS      ?= $(LINT_TARGETS)
RADON_TARGETS          ?= $(LINT_TARGETS)
PYDOCSTYLE_TARGETS     ?= $(LINT_TARGETS)
LINT_PRE_TARGETS       ?=

LINT_ARTIFACTS_DIR     ?= artifacts/lint
FMT_LOG                ?= $(LINT_ARTIFACTS_DIR)/fmt.log
RUFF_CACHE_DIR         ?= $(LINT_ARTIFACTS_DIR)/.ruff_cache
MYPY_CACHE_DIR         ?= $(LINT_ARTIFACTS_DIR)/.mypy_cache
LINT_SELF_MAKE         ?= $(MAKE)

RUFF_CONFIG            ?= configs/ruff.toml
MYPY_CONFIG            ?= configs/mypy.ini
MYPY_FLAGS             ?= --strict
PYDOCSTYLE_ARGS        ?= --convention=google --add-ignore=D100,D101,D102,D103,D104,D105,D106,D107
RADON_COMPLEXITY_MAX   ?=

ENABLE_MYPY            ?= 1
ENABLE_CODESPELL       ?= 1
ENABLE_RADON           ?= 1
ENABLE_PYDOCSTYLE      ?= 1
RUFF_CHECK_FIX         ?= 0
FMT_RUN_RUFF_CHECK_FIX ?= 0

RUFF_FIX_FLAG := $(if $(filter 1,$(RUFF_CHECK_FIX)),--fix,)

.PHONY: fmt fmt-artifacts lint lint-artifacts lint-file lint-dir lint-clean

fmt: fmt-artifacts
	@echo "✔ Formatting completed (logs in '$(FMT_LOG)')"

fmt-artifacts: | $(VENV)
	@mkdir -p "$(LINT_ARTIFACTS_DIR)" "$(RUFF_CACHE_DIR)"
	@$(RUFF) format --config "$(RUFF_CONFIG)" --cache-dir "$(RUFF_CACHE_DIR)" $(FMT_DIRS) 2>&1 | tee "$(FMT_LOG)"
	@if [ "$(FMT_RUN_RUFF_CHECK_FIX)" = "1" ]; then \
	  $(RUFF) check --config "$(RUFF_CONFIG)" --fix --cache-dir "$(RUFF_CACHE_DIR)" $(FMT_DIRS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/fmt-ruff-fix.log"; \
	fi

lint: lint-artifacts
	@echo "✔ Linting completed (logs in '$(LINT_ARTIFACTS_DIR)')"

lint-artifacts: | $(VENV)
	@mkdir -p "$(LINT_ARTIFACTS_DIR)" "$(RUFF_CACHE_DIR)" "$(MYPY_CACHE_DIR)"
	$(call run_make_targets,$(LINT_PRE_TARGETS),$(LINT_SELF_MAKE))
	@set -euo pipefail; { \
	  echo "→ Ruff format (check)"; \
	  $(RUFF) format --check --config "$(RUFF_CONFIG)" --cache-dir "$(RUFF_CACHE_DIR)" $(LINT_TARGETS); \
	} 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/ruff-format.log"
	@set -euo pipefail; $(RUFF) check $(RUFF_FIX_FLAG) --config "$(RUFF_CONFIG)" --cache-dir "$(RUFF_CACHE_DIR)" $(LINT_TARGETS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/ruff.log"
	@if [ "$(ENABLE_MYPY)" = "1" ]; then \
	  set -euo pipefail; $(MYPY) --config-file "$(MYPY_CONFIG)" $(MYPY_FLAGS) --cache-dir "$(MYPY_CACHE_DIR)" $(MYPY_TARGETS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/mypy.log"; \
	else \
	  echo "→ Skipping mypy" | tee "$(LINT_ARTIFACTS_DIR)/mypy.log"; \
	fi
	@if [ "$(ENABLE_CODESPELL)" = "1" ]; then \
	  set -euo pipefail; $(CODESPELL) $(CODESPELL_TARGETS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/codespell.log"; \
	else \
	  echo "→ Skipping codespell" | tee "$(LINT_ARTIFACTS_DIR)/codespell.log"; \
	fi
	@if [ "$(ENABLE_RADON)" = "1" ]; then \
	  set -euo pipefail; $(RADON) cc -s -a $(RADON_TARGETS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/radon.log"; \
	  if [ -n "$(RADON_COMPLEXITY_MAX)" ]; then \
	    $(RADON) cc -j $(RADON_TARGETS) | $(VENV_PYTHON) -c 'import json, sys; payload=json.load(sys.stdin); max_score=int(sys.argv[1]); violations=[]; [violations.append((path, item.get("name"), item.get("complexity", 0))) for path, items in payload.items() for item in items if item.get("type") in {"function", "method"} and item.get("complexity", 0) > max_score]; print(f"Radon complexity threshold exceeded (>{max_score})") if violations else None; [print(f"{path}: {name} ({complexity})") for path, name, complexity in violations]; sys.exit(1 if violations else 0)' "$(RADON_COMPLEXITY_MAX)"; \
	  fi; \
	else \
	  echo "→ Skipping radon" | tee "$(LINT_ARTIFACTS_DIR)/radon.log"; \
	fi
	@if [ "$(ENABLE_PYDOCSTYLE)" = "1" ]; then \
	  set -euo pipefail; $(PYDOCSTYLE) $(PYDOCSTYLE_ARGS) $(PYDOCSTYLE_TARGETS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/pydocstyle.log"; \
	else \
	  echo "→ Skipping pydocstyle" | tee "$(LINT_ARTIFACTS_DIR)/pydocstyle.log"; \
	fi
	@[ -d .mypy_cache ] && echo "→ removing stray .mypy_cache" && rm -rf .mypy_cache || true
	@[ -d .ruff_cache ] && echo "→ removing stray .ruff_cache" && rm -rf .ruff_cache || true
	@printf "OK\n" > "$(LINT_ARTIFACTS_DIR)/_passed"

lint-file:
ifndef file
	$(error Usage: make lint-file file=path/to/file.py)
endif
	@$(MAKE) LINT_SCOPE="$(file)" lint-artifacts

lint-dir:
ifndef dir
	$(error Usage: make lint-dir dir=<directory_path>)
endif
	@$(MAKE) LINT_SCOPE="$(dir)" lint-artifacts

lint-clean:
	@echo "→ Cleaning lint artifacts"
	@rm -rf "$(LINT_ARTIFACTS_DIR)" .mypy_cache .ruff_cache || true
	@echo "✔ done"

##@ Lint
fmt: ## Apply Ruff formatting; save logs to artifacts/lint/fmt.log
lint: ## Run all lint checks; save logs to artifacts/lint/
lint-artifacts: ## Same as 'lint' (explicit), generates logs
lint-file: ## Lint a single file (requires file=<path>)
lint-dir: ## Lint a directory (requires dir=<path>)
lint-clean: ## Remove lint artifacts, including caches
