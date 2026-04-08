# Build Configuration — keep outputs under artifacts/

# Dirs & flags
BUILD_DIR        ?= artifacts/build
PACKAGE_DIR      ?=
PACKAGE_NAME     ?=
CHECK_DISTS      ?= 0             # set to 0 to skip twine check by default
ROOT_BUILD_PACKAGE_DIRS ?= \
	packages/agentic-proteins \
	packages/bijux-proteomics-foundation \
	packages/bijux-proteomics-core \
	packages/bijux-proteomics-intelligence \
	packages/bijux-proteomics-knowledge \
	packages/bijux-proteomics-lab

# Absolute paths (safer if a target changes CWD)
BUILD_DIR_ABS    := $(abspath $(BUILD_DIR))

.PHONY: build build-sdist build-wheel build-check build-tools build-clean release-dry
.PHONY: build-package build-agentic-proteins build-bijux-proteomics-foundation build-bijux-proteomics-core build-bijux-proteomics-intelligence build-bijux-proteomics-knowledge build-bijux-proteomics-lab

build: build-tools
	@set -euo pipefail; \
	for package_dir in $(ROOT_BUILD_PACKAGE_DIRS); do \
	  package_name="$$(basename "$$package_dir")"; \
	  $(MAKE) build-package PACKAGE_DIR="$$package_dir" PACKAGE_NAME="$$package_name"; \
	done; \
	echo "✔ Build artifacts ready in '$(BUILD_DIR_ABS)'"

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
	@$(VENV_PYTHON) -m build --version >/dev/null
	@$(VENV_PYTHON) -m twine --version >/dev/null

build-sdist: build
	@true

build-wheel: build
	@true

build-check:
	@if find "$(BUILD_DIR_ABS)" -mindepth 2 -maxdepth 2 \( -name '*.whl' -o -name '*.tar.gz' \) -print -quit | grep -q .; then \
	  find "$(BUILD_DIR_ABS)" -mindepth 2 -maxdepth 2 \( -name '*.whl' -o -name '*.tar.gz' \) -print0 | xargs -0 "$(VENV_PYTHON)" -m twine check 2>&1 | tee "$(BUILD_DIR_ABS)/twine-check.log"; \
	else \
	  echo "✘ No artifacts in $(BUILD_DIR_ABS) to check"; exit 1; \
	fi

release-dry: build-agentic-proteins
	@echo "→ Release dry-run checks..."
	@$(VENV_PYTHON) -c 'from packaging.version import Version; import importlib.metadata as m; from pathlib import Path; import sys; version=m.version("agentic-proteins"); base=Version(version).base_version; print(f"version={version} base={base}"); changelog=Path("packages/agentic-proteins/CHANGELOG.md").read_text().splitlines(); header=f"## {base}"; sys.exit(f"Missing changelog header for {base}") if header not in changelog else None; idx=changelog.index(header); section_lines=changelog[idx + 1:]; end_idx=next((i for i, line in enumerate(section_lines) if line.startswith("## ")), None); section="\\n".join(section_lines[:end_idx] if end_idx is not None else section_lines); required=["### Added","### Changed","### Fixed"]; missing=[h for h in required if h not in section]; sys.exit(f"Changelog {base} missing sections: {missing}") if missing else None; print("✔ Changelog sections present")'
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
build-tools: ## Ensure the uv environment has build and Twine commands available
build-clean: ## Remove ALL build artifacts (artifacts/build + temporary files)
clean-temp-build-files: ## (Internal) Remove temporary build files from the root directory
build: ## Build wheel and sdist artifacts for every publishable package
build-package: ## Build wheel and sdist for PACKAGE_DIR into artifacts/build/<package>
build-agentic-proteins: ## Build wheel and sdist for packages/agentic-proteins
build-bijux-proteomics-foundation: ## Build wheel and sdist for packages/bijux-proteomics-foundation
build-bijux-proteomics-core: ## Build wheel and sdist for packages/bijux-proteomics-core
build-bijux-proteomics-intelligence: ## Build wheel and sdist for packages/bijux-proteomics-intelligence
build-bijux-proteomics-knowledge: ## Build wheel and sdist for packages/bijux-proteomics-knowledge
build-bijux-proteomics-lab: ## Build wheel and sdist for packages/bijux-proteomics-lab
build-sdist: ## Build all package source distributions through the standard build flow
build-wheel: ## Build all package wheels through the standard build flow
build-check: ## Run twine check on all built distributions under artifacts/build/*
release-dry: ## Build agentic-proteins and validate version + changelog (no upload)
