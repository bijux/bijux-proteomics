# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

TEST_PATHS                ?= packages/agentic-proteins/tests packages/bijux-proteomics-dev/tests packages/bijux-proteomics-foundation/tests packages/bijux-proteomics-core/tests packages/bijux-proteomics-intelligence/tests packages/bijux-proteomics-knowledge/tests packages/bijux-proteomics-lab/tests
TEST_PATHS_UNIT           ?= packages/agentic-proteins/tests/unit
TEST_PATHS_E2E            ?= packages/agentic-proteins/tests/e2e
TEST_PATHS_REGRESSION     ?= packages/agentic-proteins/tests/regression
TEST_PATHS_EVALUATION     ?= packages/agentic-proteins/tests/regression
TEST_REAL_LOCAL_PATH      ?= packages/agentic-proteins/tests/real_local
TEST_MAIN_ARGS            ?= -m "not real_local"
TEST_CI_TARGETS           ?= test-unit test-e2e test-regression test-evaluation
TEST_COVERAGE_FAIL_UNDER  ?= 60
TEST_SOURCE_PATHS         ?= packages/agentic-proteins/src packages/bijux-proteomics-dev/src packages/bijux-proteomics-foundation/src packages/bijux-proteomics-core/src packages/bijux-proteomics-intelligence/src packages/bijux-proteomics-knowledge/src packages/bijux-proteomics-lab/src
PYTEST_ADDOPTS_EXTRA      ?= --rootdir "$(abspath .)"
PYTEST_CONFIG             ?= $(CONFIG_DIR)/pytest.ini
COVERAGE_CONFIG           ?= $(CONFIG_DIR)/coveragerc.ini

include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/bijux-py/test.mk
