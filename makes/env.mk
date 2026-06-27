BIJUX_REPOSITORY_ENV_OVERLAY_INCLUDED := 1

MONOREPO_ROOT := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))/..)
ROOT_MAKE_DIR := $(MONOREPO_ROOT)/makes
QUALITY_GATE_PYTHON ?= $(if $(and $(ROOT_CHECK_PYTHON),$(wildcard $(ROOT_CHECK_PYTHON))),$(abspath $(ROOT_CHECK_PYTHON)),$(if $(wildcard $(VENV_PYTHON)),$(abspath $(VENV_PYTHON)),$(if $(wildcard $(VENV)/bin/python),$(abspath $(VENV)/bin/python),$(PYTHON))))
DEPTRY_SCAN_SCRIPT ?= PYTHONPATH="$(MONOREPO_ROOT)/packages/bijux-proteomics-dev/src$${PYTHONPATH:+:$$PYTHONPATH}" "$(QUALITY_GATE_PYTHON)" -m bijux_proteomics_dev.quality.dependencies.deptry_scan
DEPTRY_CONFIG ?= $(MONOREPO_ROOT)/configs/deptry.toml
QUALITY_DEPTRY_COMMAND ?= $(DEPTRY_SCAN_SCRIPT) --config "$(DEPTRY_CONFIG)" --project-dir . $(QUALITY_PATHS)
QUALITY_DEPTRY_VERSION_COMMAND ?=
CODESPELL ?= $(VENV_PYTHON) -m codespell_lib
PIP_AUDIT_PYTHON ?= $(QUALITY_GATE_PYTHON)
PIP_AUDIT ?= env VIRTUAL_ENV= "$(PIP_AUDIT_PYTHON)" -m pip_audit
SBOM_PIP_AUDIT ?= env VIRTUAL_ENV= "$(PIP_AUDIT_PYTHON)" -m pip_audit
SECURITY_AUDIT_PREPARE_MODE ?= environment
PIP_AUDIT_INPUTS ?=
SECURITY_PIP_AUDIT_TEXT_COMMAND ?= VIRTUAL_ENV= PYTHONPATH="$(MONOREPO_ROOT)/packages/bijux-proteomics-dev/src$${PYTHONPATH:+:$$PYTHONPATH}" "$(PIP_AUDIT_PYTHON)" -m bijux_proteomics_dev.security.pip_audit_gate

include $(ROOT_MAKE_DIR)/bijux-py/repository/env.mk
