PACKAGE_KIND ?= repository-python
MYPY_CONFIG ?= $(MONOREPO_ROOT)/configs/mypy.ini
API_MODE ?= freeze
TEST_MAIN_ARGS ?= -m "unit and not slow and not benchmark and not external_data and not governance and not real_local and not api"
TEST_E2E_ARGS ?= -m "e2e and not slow" --maxfail=1 -q
TEST_REGRESSION_ARGS ?= -m "regression and not slow" --maxfail=1 -q
TEST_EVALUATION_ARGS ?= -m "evaluation and not slow" --maxfail=1 -q
TEST_REAL_LOCAL_ARGS ?= -m "real_local and not slow" -s -p no:cov
ENABLE_MYPY ?= 1
PYDOCSTYLE_ARGS ?= --convention=google --add-ignore=D100,D101,D102,D103,D104,D105,D106,D107,D202
ENABLE_PYDOCSTYLE ?= 1
QUALITY_MYPY_CONFIG ?= $(MYPY_CONFIG)
QUALITY_MYPY_TARGETS ?= $(QUALITY_PATHS)
QUALITY_VULTURE_MIN_CONFIDENCE ?= 90
SECURITY_IGNORE_IDS ?= PYSEC-2022-42969 CVE-2025-68463
SECURITY_AUDIT_PREPARE_MODE ?= environment
PIP_AUDIT_INPUTS ?=
SECURITY_BANDIT_SKIP_IDS ?= B311
BUILD_PER_PACKAGE_DIRS ?= 1
API_FREEZE_COMMAND ?= $(VENV_PYTHON) -m bijux_proteomics_dev.governance.contracts.freeze_contracts
API_OPENAPI_DRIFT_COMMAND ?= $(VENV_PYTHON) -m bijux_proteomics_dev.governance.contracts.openapi_drift
PACKAGE_ARTIFACT_ALIAS_SCRIPT ?= $(MONOREPO_ROOT)/makes/repository_artifact_layout.py

test-all: TEST_MAIN_ARGS =
test-all: PYTEST_ADDOPTS_EXTRA = -o timeout=0
test-all: test
.PHONY: test-all

test-all-plus-run-time: TEST_MAIN_ARGS =
test-all-plus-run-time: PYTEST_ADDOPTS_EXTRA = -o timeout=0 --durations=0 --durations-min=0
test-all-plus-run-time: test
.PHONY: test-all-plus-run-time

test-slow: TEST_MAIN_ARGS = -m "slow or benchmark or external_data"
test-slow: PYTEST_ADDOPTS_EXTRA = -o timeout=0 --durations=0 --durations-min=0
test-slow: test
.PHONY: test-slow
