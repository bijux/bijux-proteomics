include $(abspath $(dir $(lastword $(MAKEFILE_LIST))))/api-env.mk

ifeq ($(strip $(API_REPO_DIR)),)
$(error API_REPO_DIR is required before including bijux-py/api.mk)
endif

ifeq ($(API_MODE),contract)
include $(API_REPO_DIR)/contract.mk
else ifeq ($(API_MODE),live-contract)
include $(API_REPO_DIR)/live-contract.mk
else ifeq ($(API_MODE),freeze)
include $(API_REPO_DIR)/freeze.mk
else
$(error Unsupported API_MODE '$(API_MODE)'; expected contract, live-contract, or freeze)
endif
