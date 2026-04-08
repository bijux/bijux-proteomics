# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

.DELETE_ON_ERROR:
.DEFAULT_GOAL := all
.SHELLFLAGS := -eu -o pipefail -c
SHELL := bash

PYTHON ?= python3.11
UV ?= uv
RM ?= rm -rf

.NOTPARALLEL: all clean

VENV ?= .venv
VENV_PYTHON ?= $(if $(shell test -x "$(VENV)/bin/python" && echo yes),$(VENV)/bin/python,python3)
ACT ?= $(if $(wildcard $(VENV)/bin/activate),$(VENV)/bin,)
CONFIG_DIR ?= configs
DEV_PYTHONPATH ?= packages/bijux-proteomics-dev/src
DEV_RUN ?= PYTHONPATH="$(DEV_PYTHONPATH)$${PYTHONPATH:+:$$PYTHONPATH}" "$(VENV_PYTHON)"
COMMA := ,
UV_GROUPS ?= $(if $(strip $(EXTRAS)),$(subst $(COMMA), ,$(EXTRAS)),dev)
UV_SYNC_FLAGS := $(foreach group,$(UV_GROUPS),--group $(group))
UV_SYNC ?= UV_PROJECT_ENVIRONMENT=$(VENV) $(UV) sync --frozen --python $(PYTHON) $(UV_SYNC_FLAGS)

-include .env
export
