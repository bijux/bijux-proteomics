# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

ROOT_MAKEFILE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

include $(ROOT_MAKEFILE_DIR)/root/env.mk
include $(ROOT_MAKEFILE_DIR)/root/targets.mk
include $(ROOT_MAKEFILE_DIR)/bijux-py/standard.mk
