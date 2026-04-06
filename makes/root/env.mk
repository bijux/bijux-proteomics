# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

.DELETE_ON_ERROR:
.DEFAULT_GOAL := all
.SHELLFLAGS := -eu -o pipefail -c
SHELL := bash

PYTHON ?= python3.11
RM ?= rm -rf
SETUPTOOLS_VERSION ?= <82

.NOTPARALLEL: all clean

VENV ?= .venv
VENV_PYTHON ?= $(if $(shell test -x "$(VENV)/bin/python" && echo yes),$(VENV)/bin/python,python3)
ACT ?= $(if $(wildcard $(VENV)/bin/activate),$(VENV)/bin,)

-include .env
export
