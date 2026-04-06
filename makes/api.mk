# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

API_MODE ?= freeze
API_ARTIFACTS_DIR ?= artifacts/api
API_LINT_DIR ?= $(API_ARTIFACTS_DIR)/lint
API_TEST_DIR ?= $(API_ARTIFACTS_DIR)/test
API_LOG ?= $(API_ARTIFACTS_DIR)/server.log
API_MAKEFILE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

ifeq ($(API_MODE),contract)
include $(API_MAKEFILE_DIR)/api/contract.mk
else ifeq ($(API_MODE),live-contract)
include $(API_MAKEFILE_DIR)/api/live-contract.mk
else ifeq ($(API_MODE),freeze)
include $(API_MAKEFILE_DIR)/api/freeze.mk
else
$(error Unsupported API_MODE '$(API_MODE)'; expected contract, live-contract, or freeze)
endif
