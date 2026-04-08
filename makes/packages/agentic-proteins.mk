include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/../package/profile.mk
include $(ROOT_MAKE_DIR)/package/python-package.mk

PACKAGE_IMPORT_NAME := agentic_proteins
PACKAGE_INSTALL_SPEC := .
PACKAGE_INSTALL_PYTHON_PACKAGES := $(MONOREPO_ROOT)/packages/bijux-proteomics-dev
RUFF_CONFIG := $(MONOREPO_ROOT)/configs/ruff.toml
MYPY_CONFIG := $(MONOREPO_ROOT)/configs/mypy.ini
PYDOCSTYLE_ARGS := --convention=google --add-ignore=D100,D101,D102,D103,D104,D105,D106,D107
ENABLE_PYDOCSTYLE := 1
TEST_PATHS := tests
TEST_PATHS_UNIT := tests/unit
TEST_PATHS_E2E := tests/e2e
TEST_PATHS_REGRESSION := tests/regression
TEST_PATHS_EVALUATION := tests/regression
TEST_REAL_LOCAL_PATH := tests/real_local
TEST_MAIN_ARGS := -m "not real_local"
TEST_CI_TARGETS := test-unit test-e2e test-regression test-evaluation
TEST_COVERAGE_FAIL_UNDER := 60
TEST_SOURCE_PATHS := src
INTERROGATE_PATHS := src
QUALITY_PATHS := src
QUALITY_MYPY_CONFIG := $(MONOREPO_ROOT)/configs/mypy.ini
QUALITY_MYPY_TARGETS := $(QUALITY_PATHS)
QUALITY_VULTURE_MIN_CONFIDENCE := 90
SECURITY_PATHS := src
SECURITY_IGNORE_IDS := PYSEC-2022-42969 CVE-2025-68463
SECURITY_BANDIT_SKIP_IDS := B311
SECURITY_PIP_AUDIT_TEXT_COMMAND := PYTHONPATH="$(MONOREPO_ROOT)/packages/bijux-proteomics-dev/src$${PYTHONPATH:+:$$PYTHONPATH}" "$(VENV_PYTHON)" -m bijux_proteomics_dev.security.pip_audit_gate
BUILD_DIR := $(MONOREPO_ROOT)/artifacts/build
BUILD_PER_PACKAGE_DIRS := 1
SBOM_DIR := $(MONOREPO_ROOT)/artifacts/sbom
API_MODE := freeze
API_FREEZE_COMMAND := $(VENV_PYTHON) -m bijux_proteomics_dev.api.freeze_contracts
API_OPENAPI_DRIFT_COMMAND := $(VENV_PYTHON) -m bijux_proteomics_dev.api.openapi_drift

include $(ROOT_MAKE_DIR)/package/gates.mk
