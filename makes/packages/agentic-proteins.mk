include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../proteomics-package.mk

PACKAGE_IMPORT_NAME := agentic_proteins
PACKAGE_INSTALL_PYTHON_PACKAGES = "$(MONOREPO_ROOT)/packages/bijux-proteomics-dev[dev]"
TEST_PATHS := tests/package
TEST_PATHS_UNIT := tests/package
TEST_PATHS_E2E :=
TEST_PATHS_REGRESSION :=
TEST_PATHS_EVALUATION :=
TEST_REAL_LOCAL_PATH := tests/real_local
TEST_MAIN_ARGS := -m "unit and not slow and not benchmark and not external_data and not real_local"
TEST_CI_TARGETS := test-unit
TEST_COVERAGE_FAIL_UNDER := 60

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
