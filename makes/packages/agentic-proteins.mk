include $(ROOT_MAKE_DIR)/proteomics-package.mk

PACKAGE_IMPORT_NAME := agentic_proteins
PACKAGE_INSTALL_PYTHON_PACKAGES := "$(MONOREPO_ROOT)/packages/bijux-proteomics-dev[dev]"
TEST_PATHS_UNIT := tests/unit
TEST_PATHS_E2E := tests/e2e
TEST_PATHS_REGRESSION := tests/regression
TEST_PATHS_EVALUATION := tests/regression
TEST_REAL_LOCAL_PATH := tests/real_local
TEST_MAIN_ARGS := -m "not real_local"
TEST_CI_TARGETS := test-unit test-e2e test-regression test-evaluation
TEST_COVERAGE_FAIL_UNDER := 60

include $(abspath $(dir $(firstword $(MAKEFILE_LIST))))/../bijux-py/package.mk
