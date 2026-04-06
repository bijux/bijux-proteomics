# Quality Configuration (evidence → artifacts_pages/quality)

INTERROGATE_PATHS ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab
QUALITY_PATHS     ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab

VULTURE     := $(if $(ACT),$(ACT)/vulture,vulture)
DEPTRY      := $(if $(ACT),$(ACT)/deptry,deptry)
INTERROGATE := $(if $(ACT),$(ACT)/interrogate,interrogate)
MYPY        := $(if $(ACT),$(ACT)/mypy,mypy)
PYTHON      := $(shell command -v python3 || command -v python)

QUALITY_ARTIFACTS_DIR ?= artifacts/quality
QUALITY_OK_MARKER     := $(QUALITY_ARTIFACTS_DIR)/_passed
MYPY_CACHE_DIR        ?= $(QUALITY_ARTIFACTS_DIR)/.mypy_cache

SKIP_DEPTRY       ?= 0
SKIP_INTERROGATE  ?= 0
SKIP_MYPY         ?= 0

ifeq ($(shell uname -s),Darwin)
  BREW_PREFIX  := $(shell command -v brew >/dev/null 2>&1 && brew --prefix)
  CAIRO_PREFIX := $(shell test -n "$(BREW_PREFIX)" && brew --prefix cairo)
  QUALITY_ENV  := DYLD_FALLBACK_LIBRARY_PATH="$(BREW_PREFIX)/lib:$(CAIRO_PREFIX)/lib:$$DYLD_FALLBACK_LIBRARY_PATH"
else
  QUALITY_ENV  :=
endif

.PHONY: quality interrogate-report docs-links quality-clean

quality:
	@echo "→ Running quality checks..."
	@mkdir -p "$(QUALITY_ARTIFACTS_DIR)" "$(MYPY_CACHE_DIR)"

	@echo "   - Static typing (Mypy)"
	@if [ "$(SKIP_MYPY)" = "1" ]; then \
	  echo "   • SKIP_MYPY=1; skipping Mypy" | tee "$(QUALITY_ARTIFACTS_DIR)/mypy.log"; \
	else \
	  set -euo pipefail; $(MYPY) --config-file "$(CONFIG_DIR)/mypy.ini" --strict --cache-dir "$(MYPY_CACHE_DIR)" $(QUALITY_PATHS) 2>&1 | tee "$(QUALITY_ARTIFACTS_DIR)/mypy.log"; \
	fi

	@echo "   - Dead code analysis (Vulture)"
	@set -euo pipefail; \
	  { $(VULTURE) --version 2>/dev/null || echo vulture; } >"$(QUALITY_ARTIFACTS_DIR)/vulture.log"; \
	  OUT="$$( $(VULTURE) $(QUALITY_PATHS) --min-confidence 90 2>&1 || true )"; \
	  printf '%s\n' "$$OUT" >>"$(QUALITY_ARTIFACTS_DIR)/vulture.log"; \
	  if [ -z "$$OUT" ]; then echo "✔ Vulture: no dead code found." >>"$(QUALITY_ARTIFACTS_DIR)/vulture.log"; fi

	@echo "   - Dependency hygiene (Deptry)"
	@if [ "$(SKIP_DEPTRY)" = "1" ]; then \
	  echo "   • SKIP_DEPTRY=1; skipping Deptry" | tee "$(QUALITY_ARTIFACTS_DIR)/deptry.log"; \
	else \
	  set -euo pipefail; \
	    { $(DEPTRY) --version 2>/dev/null || true; } >"$(QUALITY_ARTIFACTS_DIR)/deptry.log"; \
	    $(DEPTRY) $(QUALITY_PATHS) 2>&1 | tee -a "$(QUALITY_ARTIFACTS_DIR)/deptry.log"; \
	fi

	@echo "   - Documentation coverage (Interrogate)"
	@if [ "$(SKIP_INTERROGATE)" = "1" ]; then \
	  echo "   • SKIP_INTERROGATE=1; skipping Interrogate" | tee "$(QUALITY_ARTIFACTS_DIR)/interrogate.full.txt"; \
	else \
	  $(MAKE) interrogate-report; \
	fi

	@echo "   - Markdown link check"
	@$(PYTHON) scripts/check_md_links.py

	@echo "   - Documentation consistency"
	@$(PYTHON) scripts/check_docs_consistency.py

	@echo "   - MkDocs build"
	@$(PYTHON) -m mkdocs build --strict

	@echo "✔ Quality checks passed"
	@printf "OK\n" >"$(QUALITY_OK_MARKER)"

interrogate-report:
	@echo "→ Generating docstring coverage report (<100%)"
	@mkdir -p "$(QUALITY_ARTIFACTS_DIR)"
	@set +e; \
	  OUT="$$( $(QUALITY_ENV) $(INTERROGATE) --verbose $(INTERROGATE_PATHS) )"; \
	  rc=$$?; \
	  printf '%s\n' "$$OUT" >"$(QUALITY_ARTIFACTS_DIR)/interrogate.full.txt"; \
	  OFF="$$(printf '%s\n' "$$OUT" | awk -F'|' 'NR>3 && $$0 ~ /^\|/ { \
	    name=$$2; cov=$$6; gsub(/^[ \t]+|[ \t]+$$/, "", name); gsub(/^[ \t]+|[ \t]+$$/, "", cov); \
	    if (name !~ /^-+$$/ && cov != "100%") printf("  - %s (%s)\n", name, cov); \
	  }')"; \
	  printf '%s\n' "$$OFF" >"$(QUALITY_ARTIFACTS_DIR)/interrogate.offenders.txt"; \
	  if [ -n "$$OFF" ]; then printf '%s\n' "$$OFF"; else echo "✔ All files 100% documented"; fi; \
	  exit $$rc

docs-links:
	@$(PYTHON) scripts/check_md_links.py

quality-clean:
	@echo "→ Cleaning quality artifacts"
	@rm -rf "$(QUALITY_ARTIFACTS_DIR)"

##@ Quality
quality: ## Run Vulture, Deptry, Interrogate; save logs to artifacts_pages/quality/
interrogate-report: ## Save full Interrogate table + offenders list
docs-links: ## Fail if markdown links are broken (docs + README)
quality-clean: ## Remove artifacts_pages/quality
