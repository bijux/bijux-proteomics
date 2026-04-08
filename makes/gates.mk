PROJECT_ARTIFACTS_DIR ?= artifacts

LINT_DIRS ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab
RUFF_CONFIG ?= $(CONFIG_DIR)/ruff.toml
MYPY_CONFIG ?= $(CONFIG_DIR)/mypy.ini
PYDOCSTYLE_ARGS ?= --convention=google --add-ignore=D100,D101,D102,D103,D104,D105,D106,D107
ENABLE_PYDOCSTYLE ?= 1

include $(ROOT_MAKEFILE_DIR)/bijux-py/lint.mk

TEST_PATHS ?= packages/agentic-proteins/tests packages/bijux-proteomics-dev/tests packages/bijux-proteomics-foundation/tests packages/bijux-proteomics-core/tests packages/bijux-proteomics-intelligence/tests packages/bijux-proteomics-knowledge/tests packages/bijux-proteomics-lab/tests
TEST_PATHS_UNIT ?= packages/agentic-proteins/tests/unit
TEST_PATHS_E2E ?= packages/agentic-proteins/tests/e2e
TEST_PATHS_REGRESSION ?= packages/agentic-proteins/tests/regression
TEST_PATHS_EVALUATION ?= packages/agentic-proteins/tests/regression
TEST_REAL_LOCAL_PATH ?= packages/agentic-proteins/tests/real_local
TEST_MAIN_ARGS ?= -m "not real_local"
TEST_CI_TARGETS ?= test-unit test-e2e test-regression test-evaluation
TEST_COVERAGE_FAIL_UNDER ?= 60
TEST_SOURCE_PATHS ?= packages/agentic-proteins/src packages/bijux-proteomics-dev/src packages/bijux-proteomics-foundation/src packages/bijux-proteomics-core/src packages/bijux-proteomics-intelligence/src packages/bijux-proteomics-knowledge/src packages/bijux-proteomics-lab/src
PYTEST_ADDOPTS_EXTRA ?= --rootdir "$(abspath .)"
PYTEST_CONFIG ?= $(CONFIG_DIR)/pytest.ini
COVERAGE_CONFIG ?= $(CONFIG_DIR)/coveragerc.ini

include $(ROOT_MAKEFILE_DIR)/bijux-py/test.mk

INTERROGATE_PATHS ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab
QUALITY_PATHS ?= $(INTERROGATE_PATHS)
QUALITY_MYPY_CONFIG ?= $(CONFIG_DIR)/mypy.ini
QUALITY_MYPY_TARGETS ?= $(QUALITY_PATHS)
QUALITY_VULTURE_MIN_CONFIDENCE ?= 90
QUALITY_POST_TARGETS ?= quality-docs-links quality-docs-consistency
QUALITY_RUN_MKDOCS ?= 1
SKIP_MYPY ?= 0

include $(ROOT_MAKEFILE_DIR)/bijux-py/quality.mk

quality-docs-links:
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.markdown_links
.PHONY: quality-docs-links

quality-docs-consistency:
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.consistency
.PHONY: quality-docs-consistency

SECURITY_PATHS ?= packages/agentic-proteins/src/agentic_proteins packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation packages/bijux-proteomics-core/src/bijux_proteomics packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge packages/bijux-proteomics-lab/src/bijux_proteomics_lab
BANDIT ?= $(if $(ACT),$(ACT)/bandit,bandit)
PIP_AUDIT ?= $(if $(ACT),$(ACT)/pip-audit,pip-audit)
SECURITY_IGNORE_IDS ?= PYSEC-2022-42969 CVE-2025-68463
SECURITY_BANDIT_SKIP_IDS ?= B311
SECURITY_PIP_AUDIT_TEXT_COMMAND ?= PYTHONPATH="$(DEV_PYTHONPATH)$${PYTHONPATH:+:$$PYTHONPATH}" "$(VENV_PYTHON)" -m bijux_proteomics_dev.security.pip_audit_gate
SECURITY_EXTRA_TARGETS ?= security-dependency-allowlist

include $(ROOT_MAKEFILE_DIR)/bijux-py/security.mk

security-dependency-allowlist:
	@$(DEV_RUN) -m bijux_proteomics_dev.security.dependency_allowlist
.PHONY: security-dependency-allowlist

BUILD_DIR ?= $(PROJECT_ARTIFACTS_DIR)/build
BUILD_CHECK_DISTS ?= $(if $(filter undefined,$(origin CHECK_DISTS)),0,$(CHECK_DISTS))
BUILD_PER_PACKAGE_DIRS ?= 1
ROOT_BUILD_PACKAGE_DIRS ?= packages/agentic-proteins packages/bijux-proteomics-foundation packages/bijux-proteomics-core packages/bijux-proteomics-intelligence packages/bijux-proteomics-knowledge packages/bijux-proteomics-lab
ROOT_BUILD_ALIAS_PACKAGES ?= agentic-proteins bijux-proteomics-foundation bijux-proteomics-core bijux-proteomics-intelligence bijux-proteomics-knowledge bijux-proteomics-lab
BUILD_TOOLS_COMMAND ?= $(BUILD_PYTHON) -m build --version >/dev/null && $(BUILD_PYTHON) -m twine --version >/dev/null
BUILD_TEMP_CLEAN_PATHS ?= build dist packages/*/src/*.egg-info
BUILD_TEMP_CLEAN_PYCACHE ?= 1
BUILD_RELEASE_DRY_RUN_CMD ?= $(VENV_PYTHON) -c 'from packaging.version import Version; import importlib.metadata as m; from pathlib import Path; import sys; version=m.version("agentic-proteins"); base=Version(version).base_version; print(f"version={version} base={base}"); changelog=Path("packages/agentic-proteins/CHANGELOG.md").read_text().splitlines(); header=f"## {base}"; sys.exit(f"Missing changelog header for {base}") if header not in changelog else None; idx=changelog.index(header); section_lines=changelog[idx + 1:]; end_idx=next((i for i, line in enumerate(section_lines) if line.startswith("## ")), None); section="\n".join(section_lines[:end_idx] if end_idx is not None else section_lines); required=["### Added","### Changed","### Fixed"]; missing=[h for h in required if h not in section]; sys.exit(f"Changelog {base} missing sections: {missing}") if missing else None; print("✔ Changelog sections present")'

include $(ROOT_MAKEFILE_DIR)/bijux-py/build.mk

clean-temp-build-files: build-clean-temp
.PHONY: clean-temp-build-files

PACKAGE_NAME ?= agentic_proteins
GIT_TAG_EXACT := $(shell git describe --tags --exact-match 2>/dev/null | sed -E 's/^v//')
GIT_TAG_LATEST := $(shell git describe --tags --abbrev=0 2>/dev/null | sed -E 's/^v//')
PYPROJECT_VERSION = $(call read_pyproject_version)
PKG_VERSION ?= $(if $(GIT_TAG_EXACT),$(GIT_TAG_EXACT),$(if $(PYPROJECT_VERSION),$(PYPROJECT_VERSION),$(if $(GIT_TAG_LATEST),$(GIT_TAG_LATEST),0.0.0)))
GIT_DESCRIBE := $(shell git describe --tags --long --dirty --always 2>/dev/null)
PKG_VERSION_FULL := $(if $(GIT_TAG_EXACT),$(PKG_VERSION),$(shell echo "$(GIT_DESCRIBE)" | sed -E 's/^v//; s/-([0-9]+)-g([0-9a-f]+)(-dirty)?$$/+\1.g\2\3/'))
SBOM_VERSION ?= $(if $(PKG_VERSION_FULL),$(PKG_VERSION_FULL),$(PKG_VERSION))
SBOM_DIR ?= $(PROJECT_ARTIFACTS_DIR)/sbom
SBOM_PROD_REQ_INPUT ?= requirements/prod.txt
SBOM_DEV_REQ_INPUT ?= requirements/dev.txt
SBOM_IGNORE_IDS ?= PYSEC-2022-42969
PIP_AUDIT ?= $(if $(ACT),$(ACT)/pip-audit,pip-audit)

include $(ROOT_MAKEFILE_DIR)/bijux-py/sbom.mk

DOCS_PYTHON ?= $(if $(wildcard $(VENV_PYTHON)),$(abspath $(VENV_PYTHON)),$(if $(wildcard $(VENV)/bin/python),$(abspath $(VENV)/bin/python),$(shell command -v python3 || command -v python)))
DOCS_SITE_DIR ?= $(PROJECT_ARTIFACTS_DIR)/root/docs/site
DOCS_BUILD_SITE_DIR ?= $(DOCS_SITE_DIR)
DOCS_CHECK_SITE_DIR ?= $(DOCS_SITE_DIR)
DOCS_SERVE_SITE_DIR ?= $(DOCS_SITE_DIR)
DOCS_CACHE_DIR ?= $(PROJECT_ARTIFACTS_DIR)/root/docs/.cache
DOCS_BUILD_CONFIG_FILE ?= $(MKDOCS_CFG)
DOCS_CHECK_CONFIG_FILE ?= $(MKDOCS_CFG)
DOCS_SERVE_CONFIG_FILE ?= $(MKDOCS_CFG)
DOCS_BUILD_PREPARE_TARGETS :=
DOCS_CHECK_PREPARE_TARGETS :=
DOCS_SERVE_PREPARE_TARGETS :=
DOCS_BUILD_PRE_CLEAN_PATHS ?= $(DOCS_BUILD_SITE_DIR) $(DOCS_CACHE_DIR)
DOCS_CHECK_PRE_CLEAN_PATHS ?= $(DOCS_CHECK_SITE_DIR) $(DOCS_CACHE_DIR)
DOCS_EXTRA_CLEAN_PATHS ?= $(DOCS_SITE_DIR) $(DOCS_CACHE_DIR)
DOCS_ADDR ?= 127.0.0.1:8001
DOCS_DEV_ADDR ?= $(DOCS_ADDR)

include $(ROOT_MAKEFILE_DIR)/bijux-py/docs.mk

API_MODE ?= freeze
API_REPO_DIR := $(ROOT_MAKEFILE_DIR)/api
API_FREEZE_COMMAND ?= $(DEV_RUN) -m bijux_proteomics_dev.api.freeze_contracts
API_OPENAPI_DRIFT_COMMAND ?= $(DEV_RUN) -m bijux_proteomics_dev.api.openapi_drift

include $(ROOT_MAKEFILE_DIR)/bijux-py/api.mk

.PHONY: architecture-check

architecture-check:
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.architecture_docs
	@$(DEV_RUN) -m bijux_proteomics_dev.docs.design_debt
