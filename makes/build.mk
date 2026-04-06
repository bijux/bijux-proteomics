# Build Configuration — keep outputs under artifacts/

# Dirs & flags
BUILD_DIR        ?= artifacts/build
PACKAGE_DIR      ?=
PACKAGE_NAME     ?=
CHECK_DISTS      ?= 0             # set to 0 to skip twine check by default

# Absolute paths (safer if a target changes CWD)
BUILD_DIR_ABS    := $(abspath $(BUILD_DIR))
PYPROJECT_ABS    := $(abspath pyproject.toml)

.PHONY: build build-sdist build-wheel build-check build-tools build-clean release-dry
.PHONY: build-package build-agentic-proteins build-bijux-proteomics-foundation build-bijux-proteomics-core build-bijux-proteomics-intelligence build-bijux-proteomics-knowledge build-bijux-proteomics-lab

build: build-tools
	@if [ ! -f "$(PYPROJECT_ABS)" ]; then echo "✘ pyproject.toml not found"; exit 1; fi
	@echo "→ Preparing Python package artifacts..."
	@mkdir -p "$(BUILD_DIR_ABS)"
	@echo "→ Building wheel + sdist → $(BUILD_DIR_ABS)"
	@$(VENV_PYTHON) -m build --wheel --sdist --outdir "$(BUILD_DIR_ABS)" .
	@if [ "$(CHECK_DISTS)" = "1" ]; then \
	  echo "→ Validating distributions with twine"; \
	  $(VENV_PYTHON) -m twine check "$(BUILD_DIR_ABS)"/* 2>&1 | tee "$(BUILD_DIR_ABS)/twine-check.log"; \
	else \
	  echo "→ Skipping twine check (CHECK_DISTS=$(CHECK_DISTS))"; \
	fi
	@echo "✔ Build artifacts ready in '$(BUILD_DIR_ABS)'"
	@ls -l "$(BUILD_DIR_ABS)" || true
	@$(MAKE) clean-temp-build-files # Run the corrected cleanup target

build-package: build-tools
	@if [ -z "$(PACKAGE_DIR)" ]; then echo "✘ PACKAGE_DIR is required (example: packages/agentic-proteins)"; exit 1; fi
	@if [ ! -f "$(abspath $(PACKAGE_DIR))/pyproject.toml" ]; then echo "✘ pyproject.toml not found in $(PACKAGE_DIR)"; exit 1; fi
	@package_slug="$(if $(strip $(PACKAGE_NAME)),$(PACKAGE_NAME),$(notdir $(PACKAGE_DIR)))"; \
	out_dir="$(BUILD_DIR_ABS)/$${package_slug}"; \
	echo "→ Preparing package artifacts for $(PACKAGE_DIR)"; \
	mkdir -p "$${out_dir}"; \
	$(VENV_PYTHON) -m build --wheel --sdist --outdir "$${out_dir}" "$(abspath $(PACKAGE_DIR))"; \
	if [ "$(CHECK_DISTS)" = "1" ]; then \
	  echo "→ Validating distributions with twine"; \
	  $(VENV_PYTHON) -m twine check "$${out_dir}"/* 2>&1 | tee "$${out_dir}/twine-check.log"; \
	else \
	  echo "→ Skipping twine check (CHECK_DISTS=$(CHECK_DISTS))"; \
	fi; \
	echo "✔ Package artifacts ready in '$${out_dir}'"; \
	ls -l "$${out_dir}" || true
	@$(MAKE) clean-temp-build-files

build-agentic-proteins:
	@$(MAKE) build-package PACKAGE_DIR=packages/agentic-proteins PACKAGE_NAME=agentic-proteins

build-bijux-proteomics-foundation:
	@$(MAKE) build-package PACKAGE_DIR=packages/bijux-proteomics-foundation PACKAGE_NAME=bijux-proteomics-foundation

build-bijux-proteomics-core:
	@$(MAKE) build-package PACKAGE_DIR=packages/bijux-proteomics-core PACKAGE_NAME=bijux-proteomics-core

build-bijux-proteomics-intelligence:
	@$(MAKE) build-package PACKAGE_DIR=packages/bijux-proteomics-intelligence PACKAGE_NAME=bijux-proteomics-intelligence

build-bijux-proteomics-knowledge:
	@$(MAKE) build-package PACKAGE_DIR=packages/bijux-proteomics-knowledge PACKAGE_NAME=bijux-proteomics-knowledge

build-bijux-proteomics-lab:
	@$(MAKE) build-package PACKAGE_DIR=packages/bijux-proteomics-lab PACKAGE_NAME=bijux-proteomics-lab

build-tools: | $(VENV)
	@echo "→ Ensuring build toolchain..."
	@$(VENV_PYTHON) -m pip install -U pip
	@$(VENV_PYTHON) -m pip install --upgrade build twine

build-sdist: build-tools
	@if [ ! -f "$(PYPROJECT_ABS)" ]; then echo "✘ pyproject.toml not found"; exit 1; fi
	@mkdir -p "$(BUILD_DIR_ABS)"
	@echo "→ Building sdist → $(BUILD_DIR_ABS)"
	@$(VENV_PYTHON) -m build --sdist --outdir "$(BUILD_DIR_ABS)" .
	@$(MAKE) clean-temp-build-files

build-wheel: build-tools
	@if [ ! -f "$(PYPROJECT_ABS)" ]; then echo "✘ pyproject.toml not found"; exit 1; fi
	@mkdir -p "$(BUILD_DIR_ABS)"
	@echo "→ Building wheel → $(BUILD_DIR_ABS)"
	@$(VENV_PYTHON) -m build --wheel --outdir "$(BUILD_DIR_ABS)" .
	@$(MAKE) clean-temp-build-files

build-check:
	@if ls "$(BUILD_DIR_ABS)"/* 1>/dev/null 2>&1; then \
	  $(VENV_PYTHON) -m twine check "$(BUILD_DIR_ABS)"/* 2>&1 | tee "$(BUILD_DIR_ABS)/twine-check.log"; \
	else \
	  echo "✘ No artifacts in $(BUILD_DIR_ABS) to check"; exit 1; \
	fi

release-dry: build
	@echo "→ Release dry-run checks..."
	@$(VENV_PYTHON) -c 'from packaging.version import Version; import importlib.metadata as m; from pathlib import Path; import sys; version=m.version("agentic-proteins"); base=Version(version).base_version; print(f"version={version} base={base}"); changelog=Path("CHANGELOG.md").read_text().splitlines(); header=f"## {base}"; sys.exit(f"Missing changelog header for {base}") if header not in changelog else None; idx=changelog.index(header); section_lines=changelog[idx + 1:]; end_idx=next((i for i, line in enumerate(section_lines) if line.startswith("## ")), None); section="\\n".join(section_lines[:end_idx] if end_idx is not None else section_lines); required=["### Added","### Changed","### Fixed"]; missing=[h for h in required if h not in section]; sys.exit(f"Changelog {base} missing sections: {missing}") if missing else None; print("✔ Changelog sections present")'
	@echo "✔ Release dry-run complete"

# Renamed to be more specific and corrected
clean-temp-build-files:
	@echo "→ Cleaning temporary build files from root directory..."
	@rm -rf build dist packages/*/src/*.egg-info || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✔ Temporary files cleaned."

# This target now only cleans the final output directory
build-clean:
	@echo "→ Cleaning final build artifact directory..."
	@rm -rf "$(BUILD_DIR_ABS)" || true
	@$(MAKE) clean-temp-build-files
	@echo "✔ All build artifacts cleaned."


##@ Build
build-tools: ## Ensure local venv has build tooling (pip, build, twine)
build-clean: ## Remove ALL build artifacts (artifacts/build + temporary files)
clean-temp-build-files: ## (Internal) Remove temporary build files from the root directory
build: ## Build wheel and sdist into artifacts/build and clean up temporary files
build-package: ## Build wheel and sdist for PACKAGE_DIR into artifacts/build/<package>
build-agentic-proteins: ## Build wheel and sdist for packages/agentic-proteins
build-bijux-proteomics-foundation: ## Build wheel and sdist for packages/bijux-proteomics-foundation
build-bijux-proteomics-core: ## Build wheel and sdist for packages/bijux-proteomics-core
build-bijux-proteomics-intelligence: ## Build wheel and sdist for packages/bijux-proteomics-intelligence
build-bijux-proteomics-knowledge: ## Build wheel and sdist for packages/bijux-proteomics-knowledge
build-bijux-proteomics-lab: ## Build wheel and sdist for packages/bijux-proteomics-lab
build-sdist: ## Build sdist only into artifacts/build and clean up temporary files
build-wheel: ## Build wheel only into artifacts/build and clean up temporary files
build-check: ## Run twine check on artifacts/build/*
release-dry: ## Build artifacts and validate version + changelog (no upload)
