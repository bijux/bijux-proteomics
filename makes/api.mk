API_MODE ?= freeze
API_MAKEFILE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
API_REPO_DIR := $(API_MAKEFILE_DIR)/api

include $(API_MAKEFILE_DIR)/bijux-py/api.mk
