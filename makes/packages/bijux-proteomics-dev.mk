PACKAGE_KIND := python
PACKAGE_IMPORT_NAME := bijux_proteomics_dev
PACKAGE_INSTALL_SPEC := .[dev]
RUFF_CONFIG = $(MONOREPO_ROOT)/configs/ruff.toml
MYPY_CONFIG = $(MONOREPO_ROOT)/configs/mypy.ini
ENABLE_PYDOCSTYLE := 0
TEST_PATHS := tests
TEST_MAIN_ARGS := -m "unit and not slow and not benchmark and not external_data"
TEST_SOURCE_PATHS := src
INTERROGATE_PATHS := src
QUALITY_PATHS := src tests
SECURITY_PATHS := src
SECURITY_IGNORE_IDS := PYSEC-2022-42969 CVE-2025-68463
SECURITY_AUDIT_PREPARE_MODE := environment
PIP_AUDIT_INPUTS =
SECURITY_BANDIT_SKIP_IDS := B311
PACKAGE_ALL_TARGETS := clean install test lint quality security build sbom

test-all: TEST_MAIN_ARGS =
test-all: PYTEST_ADDOPTS_EXTRA = -o timeout=0
test-all: test
.PHONY: test-all

test-all-plus-run-time: TEST_MAIN_ARGS =
test-all-plus-run-time: PYTEST_ADDOPTS_EXTRA = -o timeout=0 --durations=0 --durations-min=0
test-all-plus-run-time: test
.PHONY: test-all-plus-run-time

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
