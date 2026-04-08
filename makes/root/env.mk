# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

include $(ROOT_MAKEFILE_DIR)/bijux-py/root-env.mk

PROJECT_DIR ?= $(CURDIR)
PROJECT_SLUG ?= bijux-proteomics
PROJECT_ARTIFACTS_DIR ?= artifacts
CONFIG_DIR ?= configs
VENV ?= $(ROOT_VENV)
VENV_PYTHON ?= $(if $(shell test -x "$(VENV)/bin/python" && echo yes),$(VENV)/bin/python,python3)
ACT ?= $(if $(wildcard $(VENV)/bin/activate),$(VENV)/bin,)
DEV_PYTHONPATH ?= packages/bijux-proteomics-dev/src
DEV_RUN ?= PYTHONPATH="$(DEV_PYTHONPATH)$${PYTHONPATH:+:$$PYTHONPATH}" "$(VENV_PYTHON)"
COMMA := ,
UV_GROUPS ?= $(if $(strip $(EXTRAS)),$(subst $(COMMA), ,$(EXTRAS)),dev)
UV_SYNC_FLAGS := $(foreach group,$(UV_GROUPS),--group $(group))
UV_SYNC ?= UV_PROJECT_ENVIRONMENT=$(VENV) $(UV) sync --frozen --python $(PYTHON) $(UV_SYNC_FLAGS)
MKDOCS_CFG ?= $(PROJECT_DIR)/mkdocs.yml

-include .env
export
