PACKAGE_KIND := python
PACKAGE_IMPORT_NAME := bijux_proteomics_dev
PACKAGE_INSTALL_SPEC := .[dev]
RUFF_CONFIG = $(MONOREPO_ROOT)/configs/ruff.toml
MYPY_CONFIG = $(MONOREPO_ROOT)/configs/mypy.ini
ENABLE_PYDOCSTYLE := 0
TEST_PATHS := tests/package tests/security tests/tools
TEST_MAIN_ARGS := -m "unit and not slow and not benchmark and not external_data and not governance"
TEST_SOURCE_PATHS := src
INTERROGATE_PATHS := src
QUALITY_PATHS := src tests
SECURITY_PATHS := src
SECURITY_AUDIT_PREPARE_MODE := environment
PIP_AUDIT_INPUTS =
SECURITY_EXTRA_TARGETS += security-locked-dependencies
PACKAGE_ALL_TARGETS := clean install test lint quality security build sbom
test-all: TEST_MAIN_ARGS =
test-all: TEST_PATHS = tests
test-all: PYTEST_ADDOPTS_EXTRA = -o timeout=0
test-all: test
.PHONY: test-all

test-all-plus-run-time: TEST_MAIN_ARGS =
test-all-plus-run-time: TEST_PATHS = tests
test-all-plus-run-time: PYTEST_ADDOPTS_EXTRA = -o timeout=0 --durations=0 --durations-min=0
test-all-plus-run-time: test
.PHONY: test-all-plus-run-time

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk

security-locked-dependencies:
	@PYTHONPATH="$(MONOREPO_ROOT)/packages/bijux-proteomics-dev/src" $(VENV_PYTHON) -m bijux_proteomics_dev.security.locked_dependencies
.PHONY: security-locked-dependencies
