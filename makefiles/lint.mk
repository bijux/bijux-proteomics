# Lint Configuration (no root cache pollution)

RUFF        := $(if $(ACT),$(ACT)/ruff,ruff)
MYPY        := $(if $(ACT),$(ACT)/mypy,mypy)
CODESPELL   := $(if $(ACT),$(ACT)/codespell,codespell)
PYDOCSTYLE  := $(if $(ACT),$(ACT)/pydocstyle,pydocstyle)
RADON       := $(if $(ACT),$(ACT)/radon,radon)

# Targets & dirs
LINT_DIRS           ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab
LINT_ARTIFACTS_DIR  ?= artifacts/lint
FMT_LOG             ?= $(LINT_ARTIFACTS_DIR)/fmt.log

# Tool caches inside artifacts_pages/lint
RUFF_CACHE_DIR      ?= $(LINT_ARTIFACTS_DIR)/.ruff_cache
MYPY_CACHE_DIR      ?= $(LINT_ARTIFACTS_DIR)/.mypy_cache

# In case these are not defined elsewhere
VENV_PYTHON         ?= python3

.PHONY: fmt fmt-artifacts lint lint-artifacts lint-file lint-dir lint-clean

fmt: fmt-artifacts
	@echo "✔ Formatting completed (logs in '$(FMT_LOG)')"

fmt-artifacts: | $(VENV)
	@mkdir -p "$(LINT_ARTIFACTS_DIR)"
	@$(RUFF) format --config config/ruff.toml $(LINT_DIRS) 2>&1 | tee "$(FMT_LOG)"

lint: lint-artifacts
	@echo "✔ Linting completed (logs in '$(LINT_ARTIFACTS_DIR)')"

lint-artifacts: | $(VENV)
	@mkdir -p "$(LINT_ARTIFACTS_DIR)" "$(RUFF_CACHE_DIR)" "$(MYPY_CACHE_DIR)"
	@set -euo pipefail; { \
	  echo "→ Ruff format (check)"; \
	  $(RUFF) format --check --config config/ruff.toml --cache-dir "$(RUFF_CACHE_DIR)" $(LINT_DIRS); \
	} 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/ruff-format.log"
	@set -euo pipefail; $(RUFF) check --config config/ruff.toml --cache-dir "$(RUFF_CACHE_DIR)" $(LINT_DIRS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/ruff.log"
	@set -euo pipefail; $(MYPY) --config-file config/mypy.ini --strict --cache-dir "$(MYPY_CACHE_DIR)" $(LINT_DIRS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/mypy.log"
	@set -euo pipefail; $(CODESPELL) -I config/agentic_proteins.dic $(LINT_DIRS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/codespell.log"
	@set -euo pipefail; $(RADON) cc -s -a $(LINT_DIRS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/radon.log"
	@set -euo pipefail; $(PYDOCSTYLE) --convention=google --add-ignore=D100,D101,D102,D103,D104,D105,D106,D107 $(LINT_DIRS) 2>&1 | tee "$(LINT_ARTIFACTS_DIR)/pydocstyle.log"
	@[ -d .pytype ] && echo "→ removing stray .pytype" && rm -rf .pytype || true
	@[ -d .mypy_cache ] && echo "→ removing stray .mypy_cache" && rm -rf .mypy_cache || true
	@[ -d .ruff_cache ] && echo "→ removing stray .ruff_cache" && rm -rf .ruff_cache || true
	@printf "OK\n" > "$(LINT_ARTIFACTS_DIR)/_passed"

lint-file:
ifndef file
	$(error Usage: make lint-file file=path/to/file.py)
endif
	@$(call run_tool,RuffFormat,$(RUFF) format --check --cache-dir "$(RUFF_CACHE_DIR)")
	@$(call run_tool,Ruff,$(RUFF) check --config config/ruff.toml --cache-dir "$(RUFF_CACHE_DIR)")
	@$(call run_tool,Mypy,$(MYPY) --config-file config/mypy.ini --strict --cache-dir "$(MYPY_CACHE_DIR)")
	@$(call run_tool,Codespell,$(CODESPELL) -I config/agentic_proteins.dic)
	@$(call run_tool,Radon,$(RADON) cc -s -a)
	@$(call run_tool,Pydocstyle,$(PYDOCSTYLE) --convention=google)

lint-dir:
ifndef dir
	$(error Usage: make lint-dir dir=<directory_path>)
endif
	@$(MAKE) LINT_DIRS="$(dir)" lint-artifacts

lint-clean:
	@echo "→ Cleaning lint artifacts"
	@rm -rf "$(LINT_ARTIFACTS_DIR)" .pytype .mypy_cache .ruff_cache || true
	@echo "✔ done"

##@ Lint
fmt: ## Apply Ruff formatting; save logs to artifacts/lint/fmt.log
lint: ## Run all lint checks; save logs to artifacts_pages/lint/ (ruff/mypy caches under artifacts_pages/lint)
lint-artifacts: ## Same as 'lint' (explicit), generates logs
lint-file: ## Lint a single file (requires file=<path>)
lint-dir: ## Lint a directory (requires dir=<path>)
lint-clean: ## Remove lint artifacts_pages, including caches
