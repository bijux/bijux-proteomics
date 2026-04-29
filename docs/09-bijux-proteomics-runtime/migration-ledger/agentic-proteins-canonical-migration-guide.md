---
title: agentic-proteins Canonical Migration Guide
audience: maintainer
type: reference
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-04-29
---

# agentic-proteins Canonical Migration Guide

This guide shows how compatibility imports map back to canonical package ownership. The point is not to preserve the bridge forever; it is to make every remaining legacy path reviewable and replaceable.

## Current Posture

- total compatibility modules: 147
- forwarding-only modules: 147
- review-required modules: 0

## Migration Map

| legacy module | status | canonical target(s) | migration action |
| --- | --- | --- | --- |
| `agentic_proteins.agents` | `forwarding-only` | `bijux_proteomics_runtime.agents` | replace `agentic_proteins.agents` with `bijux_proteomics_runtime.agents` |
| `agentic_proteins.agents.analysis` | `forwarding-only` | `bijux_proteomics_runtime.agents.analysis` | replace `agentic_proteins.agents.analysis` with `bijux_proteomics_runtime.agents.analysis` |
| `agentic_proteins.agents.analysis.failure_analysis` | `forwarding-only` | `bijux_proteomics_runtime.agents.analysis.failure_analysis` | replace `agentic_proteins.agents.analysis.failure_analysis` with `bijux_proteomics_runtime.agents.analysis.failure_analysis` |
| `agentic_proteins.agents.analysis.sequence_analysis` | `forwarding-only` | `bijux_proteomics_runtime.agents.analysis.sequence_analysis` | replace `agentic_proteins.agents.analysis.sequence_analysis` with `bijux_proteomics_runtime.agents.analysis.sequence_analysis` |
| `agentic_proteins.agents.analysis.structure` | `forwarding-only` | `bijux_proteomics_runtime.agents.analysis.structure` | replace `agentic_proteins.agents.analysis.structure` with `bijux_proteomics_runtime.agents.analysis.structure` |
| `agentic_proteins.agents.base` | `forwarding-only` | `bijux_proteomics_runtime.agents.base` | replace `agentic_proteins.agents.base` with `bijux_proteomics_runtime.agents.base` |
| `agentic_proteins.agents.base.base` | `forwarding-only` | `bijux_proteomics_runtime.agents.base.base` | replace `agentic_proteins.agents.base.base` with `bijux_proteomics_runtime.agents.base.base` |
| `agentic_proteins.agents.execution` | `forwarding-only` | `bijux_proteomics_runtime.agents.execution` | replace `agentic_proteins.agents.execution` with `bijux_proteomics_runtime.agents.execution` |
| `agentic_proteins.agents.execution.coordinator` | `forwarding-only` | `bijux_proteomics_runtime.agents.execution.coordinator` | replace `agentic_proteins.agents.execution.coordinator` with `bijux_proteomics_runtime.agents.execution.coordinator` |
| `agentic_proteins.agents.planning` | `forwarding-only` | `bijux_proteomics_runtime.agents.planning` | replace `agentic_proteins.agents.planning` with `bijux_proteomics_runtime.agents.planning` |
| `agentic_proteins.agents.planning.compiler` | `forwarding-only` | `bijux_proteomics_runtime.agents.planning.compiler` | replace `agentic_proteins.agents.planning.compiler` with `bijux_proteomics_runtime.agents.planning.compiler` |
| `agentic_proteins.agents.planning.generation` | `forwarding-only` | `bijux_proteomics_runtime.agents.planning.generation` | replace `agentic_proteins.agents.planning.generation` with `bijux_proteomics_runtime.agents.planning.generation` |
| `agentic_proteins.agents.planning.planner` | `forwarding-only` | `bijux_proteomics_runtime.agents.planning.planner` | replace `agentic_proteins.agents.planning.planner` with `bijux_proteomics_runtime.agents.planning.planner` |
| `agentic_proteins.agents.planning.schemas` | `forwarding-only` | `bijux_proteomics_runtime.agents.planning.schemas` | replace `agentic_proteins.agents.planning.schemas` with `bijux_proteomics_runtime.agents.planning.schemas` |
| `agentic_proteins.agents.planning.validation` | `forwarding-only` | `bijux_proteomics_runtime.agents.planning.validation` | replace `agentic_proteins.agents.planning.validation` with `bijux_proteomics_runtime.agents.planning.validation` |
| `agentic_proteins.agents.reporting` | `forwarding-only` | `bijux_proteomics_runtime.agents.reporting` | replace `agentic_proteins.agents.reporting` with `bijux_proteomics_runtime.agents.reporting` |
| `agentic_proteins.agents.reporting.reporting` | `forwarding-only` | `bijux_proteomics_runtime.agents.reporting.reporting` | replace `agentic_proteins.agents.reporting.reporting` with `bijux_proteomics_runtime.agents.reporting.reporting` |
| `agentic_proteins.agents.schemas` | `forwarding-only` | `bijux_proteomics_runtime.agents.schemas` | replace `agentic_proteins.agents.schemas` with `bijux_proteomics_runtime.agents.schemas` |
| `agentic_proteins.agents.verification` | `forwarding-only` | `bijux_proteomics_runtime.agents.verification` | replace `agentic_proteins.agents.verification` with `bijux_proteomics_runtime.agents.verification` |
| `agentic_proteins.agents.verification.critic` | `forwarding-only` | `bijux_proteomics_runtime.agents.verification.critic` | replace `agentic_proteins.agents.verification.critic` with `bijux_proteomics_runtime.agents.verification.critic` |
| `agentic_proteins.agents.verification.input_validation` | `forwarding-only` | `bijux_proteomics_runtime.agents.verification.input_validation` | replace `agentic_proteins.agents.verification.input_validation` with `bijux_proteomics_runtime.agents.verification.input_validation` |
| `agentic_proteins.agents.verification.quality_control` | `forwarding-only` | `bijux_proteomics_runtime.agents.verification.quality_control` | replace `agentic_proteins.agents.verification.quality_control` with `bijux_proteomics_runtime.agents.verification.quality_control` |
| `agentic_proteins.api` | `forwarding-only` | `bijux_proteomics_runtime.api` | replace `agentic_proteins.api` with `bijux_proteomics_runtime.api` |
| `agentic_proteins.api.app` | `forwarding-only` | `bijux_proteomics_runtime.api.app` | replace `agentic_proteins.api.app` with `bijux_proteomics_runtime.api.app` |
| `agentic_proteins.api.deps` | `forwarding-only` | `bijux_proteomics_runtime.api.deps` | replace `agentic_proteins.api.deps` with `bijux_proteomics_runtime.api.deps` |
| `agentic_proteins.api.errors` | `forwarding-only` | `bijux_proteomics_runtime.api.errors` | replace `agentic_proteins.api.errors` with `bijux_proteomics_runtime.api.errors` |
| `agentic_proteins.api.middleware` | `forwarding-only` | `bijux_proteomics_runtime.api.middleware` | replace `agentic_proteins.api.middleware` with `bijux_proteomics_runtime.api.middleware` |
| `agentic_proteins.api.v1` | `forwarding-only` | `bijux_proteomics_runtime.api.v1` | replace `agentic_proteins.api.v1` with `bijux_proteomics_runtime.api.v1` |
| `agentic_proteins.api.v1.endpoints` | `forwarding-only` | `bijux_proteomics_runtime.api.v1.endpoints` | replace `agentic_proteins.api.v1.endpoints` with `bijux_proteomics_runtime.api.v1.endpoints` |
| `agentic_proteins.api.v1.endpoints.compare` | `forwarding-only` | `bijux_proteomics_runtime.api.v1.endpoints.compare` | replace `agentic_proteins.api.v1.endpoints.compare` with `bijux_proteomics_runtime.api.v1.endpoints.compare` |
| `agentic_proteins.api.v1.endpoints.inspect` | `forwarding-only` | `bijux_proteomics_runtime.api.v1.endpoints.inspect` | replace `agentic_proteins.api.v1.endpoints.inspect` with `bijux_proteomics_runtime.api.v1.endpoints.inspect` |
| `agentic_proteins.api.v1.endpoints.resume` | `forwarding-only` | `bijux_proteomics_runtime.api.v1.endpoints.resume` | replace `agentic_proteins.api.v1.endpoints.resume` with `bijux_proteomics_runtime.api.v1.endpoints.resume` |
| `agentic_proteins.api.v1.endpoints.run` | `forwarding-only` | `bijux_proteomics_runtime.api.v1.endpoints.run` | replace `agentic_proteins.api.v1.endpoints.run` with `bijux_proteomics_runtime.api.v1.endpoints.run` |
| `agentic_proteins.api.v1.router` | `forwarding-only` | `bijux_proteomics_runtime.api.v1.router` | replace `agentic_proteins.api.v1.router` with `bijux_proteomics_runtime.api.v1.router` |
| `agentic_proteins.api.v1.schema` | `forwarding-only` | `bijux_proteomics_runtime.api.v1.schema` | replace `agentic_proteins.api.v1.schema` with `bijux_proteomics_runtime.api.v1.schema` |
| `agentic_proteins.biology` | `forwarding-only` | `bijux_proteomics.biology` | replace `agentic_proteins.biology` with `bijux_proteomics.biology` |
| `agentic_proteins.biology.pathway` | `forwarding-only` | `bijux_proteomics.biology.pathway` | replace `agentic_proteins.biology.pathway` with `bijux_proteomics.biology.pathway` |
| `agentic_proteins.biology.protein_agent` | `forwarding-only` | `bijux_proteomics.biology.protein_agent` | replace `agentic_proteins.biology.protein_agent` with `bijux_proteomics.biology.protein_agent` |
| `agentic_proteins.biology.regulator` | `forwarding-only` | `bijux_proteomics.biology.regulator` | replace `agentic_proteins.biology.regulator` with `bijux_proteomics.biology.regulator` |
| `agentic_proteins.biology.signals` | `forwarding-only` | `bijux_proteomics.biology.signals` | replace `agentic_proteins.biology.signals` with `bijux_proteomics.biology.signals` |
| `agentic_proteins.biology.validation` | `forwarding-only` | `bijux_proteomics.biology.validation` | replace `agentic_proteins.biology.validation` with `bijux_proteomics.biology.validation` |
| `agentic_proteins.core` | `forwarding-only` | `bijux_proteomics_runtime.core` | replace `agentic_proteins.core` with `bijux_proteomics_runtime.core` |
| `agentic_proteins.core.api_lock` | `forwarding-only` | `bijux_proteomics_runtime.core.api_lock` | replace `agentic_proteins.core.api_lock` with `bijux_proteomics_runtime.core.api_lock` |
| `agentic_proteins.core.contracts` | `forwarding-only` | `bijux_proteomics_runtime.core.contracts` | replace `agentic_proteins.core.contracts` with `bijux_proteomics_runtime.core.contracts` |
| `agentic_proteins.core.costs` | `forwarding-only` | `bijux_proteomics_runtime.core.costs` | replace `agentic_proteins.core.costs` with `bijux_proteomics_runtime.core.costs` |
| `agentic_proteins.core.decisions` | `forwarding-only` | `bijux_proteomics_runtime.core.decisions` | replace `agentic_proteins.core.decisions` with `bijux_proteomics_runtime.core.decisions` |
| `agentic_proteins.core.determinism` | `forwarding-only` | `bijux_proteomics_runtime.core.determinism` | replace `agentic_proteins.core.determinism` with `bijux_proteomics_runtime.core.determinism` |
| `agentic_proteins.core.execution` | `forwarding-only` | `bijux_proteomics_runtime.core.execution` | replace `agentic_proteins.core.execution` with `bijux_proteomics_runtime.core.execution` |
| `agentic_proteins.core.failures` | `forwarding-only` | `bijux_proteomics_runtime.core.failures` | replace `agentic_proteins.core.failures` with `bijux_proteomics_runtime.core.failures` |
| `agentic_proteins.core.fingerprints` | `forwarding-only` | `bijux_proteomics_runtime.core.fingerprints` | replace `agentic_proteins.core.fingerprints` with `bijux_proteomics_runtime.core.fingerprints` |
| `agentic_proteins.core.hashing` | `forwarding-only` | `bijux_proteomics_runtime.core.hashing` | replace `agentic_proteins.core.hashing` with `bijux_proteomics_runtime.core.hashing` |
| `agentic_proteins.core.identifiers` | `forwarding-only` | `bijux_proteomics_runtime.core.identifiers` | replace `agentic_proteins.core.identifiers` with `bijux_proteomics_runtime.core.identifiers` |
| `agentic_proteins.core.observations` | `forwarding-only` | `bijux_proteomics_runtime.core.observations` | replace `agentic_proteins.core.observations` with `bijux_proteomics_runtime.core.observations` |
| `agentic_proteins.core.stability` | `forwarding-only` | `bijux_proteomics_runtime.core.stability` | replace `agentic_proteins.core.stability` with `bijux_proteomics_runtime.core.stability` |
| `agentic_proteins.core.status` | `forwarding-only` | `bijux_proteomics_runtime.core.status` | replace `agentic_proteins.core.status` with `bijux_proteomics_runtime.core.status` |
| `agentic_proteins.core.surface_area` | `forwarding-only` | `bijux_proteomics_runtime.core.surface_area` | replace `agentic_proteins.core.surface_area` with `bijux_proteomics_runtime.core.surface_area` |
| `agentic_proteins.core.tooling` | `forwarding-only` | `bijux_proteomics_runtime.core.tooling` | replace `agentic_proteins.core.tooling` with `bijux_proteomics_runtime.core.tooling` |
| `agentic_proteins.design_loop` | `forwarding-only` | `bijux_proteomics_intelligence.design_loop` | replace `agentic_proteins.design_loop` with `bijux_proteomics_intelligence.design_loop` |
| `agentic_proteins.design_loop.convergence` | `forwarding-only` | `bijux_proteomics_intelligence.design_loop.convergence` | replace `agentic_proteins.design_loop.convergence` with `bijux_proteomics_intelligence.design_loop.convergence` |
| `agentic_proteins.design_loop.loop` | `forwarding-only` | `bijux_proteomics_intelligence.design_loop.loop` | replace `agentic_proteins.design_loop.loop` with `bijux_proteomics_intelligence.design_loop.loop` |
| `agentic_proteins.design_loop.stagnation` | `forwarding-only` | `bijux_proteomics_intelligence.design_loop.stagnation` | replace `agentic_proteins.design_loop.stagnation` with `bijux_proteomics_intelligence.design_loop.stagnation` |
| `agentic_proteins.domain` | `forwarding-only` | `bijux_proteomics_intelligence.domain` | replace `agentic_proteins.domain` with `bijux_proteomics_intelligence.domain` |
| `agentic_proteins.domain.candidates` | `forwarding-only` | `bijux_proteomics_intelligence.domain.candidates` | replace `agentic_proteins.domain.candidates` with `bijux_proteomics_intelligence.domain.candidates` |
| `agentic_proteins.domain.candidates.filters` | `forwarding-only` | `bijux_proteomics_intelligence.domain.candidates.filters` | replace `agentic_proteins.domain.candidates.filters` with `bijux_proteomics_intelligence.domain.candidates.filters` |
| `agentic_proteins.domain.candidates.model` | `forwarding-only` | `bijux_proteomics_intelligence.domain.candidates.model` | replace `agentic_proteins.domain.candidates.model` with `bijux_proteomics_intelligence.domain.candidates.model` |
| `agentic_proteins.domain.candidates.schema` | `forwarding-only` | `bijux_proteomics_intelligence.domain.candidates.schema` | replace `agentic_proteins.domain.candidates.schema` with `bijux_proteomics_intelligence.domain.candidates.schema` |
| `agentic_proteins.domain.candidates.selection` | `forwarding-only` | `bijux_proteomics_intelligence.domain.candidates.selection` | replace `agentic_proteins.domain.candidates.selection` with `bijux_proteomics_intelligence.domain.candidates.selection` |
| `agentic_proteins.domain.candidates.store` | `forwarding-only` | `bijux_proteomics_intelligence.domain.candidates.store` | replace `agentic_proteins.domain.candidates.store` with `bijux_proteomics_intelligence.domain.candidates.store` |
| `agentic_proteins.domain.candidates.transform` | `forwarding-only` | `bijux_proteomics_intelligence.domain.candidates.transform` | replace `agentic_proteins.domain.candidates.transform` with `bijux_proteomics_intelligence.domain.candidates.transform` |
| `agentic_proteins.domain.candidates.updates` | `forwarding-only` | `bijux_proteomics_intelligence.domain.candidates.updates` | replace `agentic_proteins.domain.candidates.updates` with `bijux_proteomics_intelligence.domain.candidates.updates` |
| `agentic_proteins.domain.confidence` | `forwarding-only` | `bijux_proteomics_knowledge.confidence` | replace `agentic_proteins.domain.confidence` with `bijux_proteomics_knowledge.confidence` |
| `agentic_proteins.domain.confidence.segments` | `forwarding-only` | `bijux_proteomics_knowledge.confidence.segments` | replace `agentic_proteins.domain.confidence.segments` with `bijux_proteomics_knowledge.confidence.segments` |
| `agentic_proteins.domain.metrics` | `forwarding-only` | `bijux_proteomics_intelligence.domain.metrics` | replace `agentic_proteins.domain.metrics` with `bijux_proteomics_intelligence.domain.metrics` |
| `agentic_proteins.domain.metrics.compute` | `forwarding-only` | `bijux_proteomics_intelligence.domain.metrics.compute` | replace `agentic_proteins.domain.metrics.compute` with `bijux_proteomics_intelligence.domain.metrics.compute` |
| `agentic_proteins.domain.metrics.quality` | `forwarding-only` | `bijux_proteomics_intelligence.domain.metrics.quality` | replace `agentic_proteins.domain.metrics.quality` with `bijux_proteomics_intelligence.domain.metrics.quality` |
| `agentic_proteins.domain.metrics.validation` | `forwarding-only` | `bijux_proteomics_intelligence.domain.metrics.validation` | replace `agentic_proteins.domain.metrics.validation` with `bijux_proteomics_intelligence.domain.metrics.validation` |
| `agentic_proteins.domain.sequence` | `forwarding-only` | `bijux_proteomics.domain.sequence` | replace `agentic_proteins.domain.sequence` with `bijux_proteomics.domain.sequence` |
| `agentic_proteins.domain.sequence.summary` | `forwarding-only` | `bijux_proteomics.domain.sequence.summary` | replace `agentic_proteins.domain.sequence.summary` with `bijux_proteomics.domain.sequence.summary` |
| `agentic_proteins.domain.sequence.validation` | `forwarding-only` | `bijux_proteomics.domain.sequence.validation` | replace `agentic_proteins.domain.sequence.validation` with `bijux_proteomics.domain.sequence.validation` |
| `agentic_proteins.domain.structure` | `forwarding-only` | `bijux_proteomics.domain.structure` | replace `agentic_proteins.domain.structure` with `bijux_proteomics.domain.structure` |
| `agentic_proteins.domain.structure.structure` | `forwarding-only` | `bijux_proteomics.domain.structure.structure` | replace `agentic_proteins.domain.structure.structure` with `bijux_proteomics.domain.structure.structure` |
| `agentic_proteins.execution` | `forwarding-only` | `bijux_proteomics_runtime.execution` | replace `agentic_proteins.execution` with `bijux_proteomics_runtime.execution` |
| `agentic_proteins.execution.compiler` | `forwarding-only` | `bijux_proteomics_runtime.execution.compiler` | replace `agentic_proteins.execution.compiler` with `bijux_proteomics_runtime.execution.compiler` |
| `agentic_proteins.execution.compiler.boundary` | `forwarding-only` | `bijux_proteomics_runtime.execution.compiler.boundary` | replace `agentic_proteins.execution.compiler.boundary` with `bijux_proteomics_runtime.execution.compiler.boundary` |
| `agentic_proteins.execution.evaluation` | `forwarding-only` | `bijux_proteomics_runtime.execution.evaluation` | replace `agentic_proteins.execution.evaluation` with `bijux_proteomics_runtime.execution.evaluation` |
| `agentic_proteins.execution.evaluation.evaluation` | `forwarding-only` | `bijux_proteomics_runtime.execution.evaluation.evaluation` | replace `agentic_proteins.execution.evaluation.evaluation` with `bijux_proteomics_runtime.execution.evaluation.evaluation` |
| `agentic_proteins.execution.evaluation.observations` | `forwarding-only` | `bijux_proteomics_runtime.execution.evaluation.observations`<br>`bijux_proteomics_runtime.execution.evaluation.observations` | replace `agentic_proteins.execution.evaluation.observations` with one of `bijux_proteomics_runtime.execution.evaluation.observations`, `bijux_proteomics_runtime.execution.evaluation.observations` |
| `agentic_proteins.execution.evaluation.schemas` | `forwarding-only` | `bijux_proteomics_runtime.execution.evaluation.schemas` | replace `agentic_proteins.execution.evaluation.schemas` with `bijux_proteomics_runtime.execution.evaluation.schemas` |
| `agentic_proteins.execution.runtime` | `forwarding-only` | `bijux_proteomics_runtime.execution.runtime` | replace `agentic_proteins.execution.runtime` with `bijux_proteomics_runtime.execution.runtime` |
| `agentic_proteins.execution.runtime.executor` | `forwarding-only` | `bijux_proteomics_runtime.execution.runtime.executor` | replace `agentic_proteins.execution.runtime.executor` with `bijux_proteomics_runtime.execution.runtime.executor` |
| `agentic_proteins.execution.runtime.integration` | `forwarding-only` | `bijux_proteomics_runtime.execution.runtime.integration` | replace `agentic_proteins.execution.runtime.integration` with `bijux_proteomics_runtime.execution.runtime.integration` |
| `agentic_proteins.execution.schemas` | `forwarding-only` | `bijux_proteomics_runtime.execution.schemas` | replace `agentic_proteins.execution.schemas` with `bijux_proteomics_runtime.execution.schemas` |
| `agentic_proteins.execution.validation` | `forwarding-only` | `bijux_proteomics_runtime.execution.validation` | replace `agentic_proteins.execution.validation` with `bijux_proteomics_runtime.execution.validation` |
| `agentic_proteins.interfaces` | `forwarding-only` | `bijux_proteomics_runtime.interfaces` | replace `agentic_proteins.interfaces` with `bijux_proteomics_runtime.interfaces` |
| `agentic_proteins.interfaces.cli` | `forwarding-only` | `bijux_proteomics_runtime.interfaces.cli` | replace `agentic_proteins.interfaces.cli` with `bijux_proteomics_runtime.interfaces.cli` |
| `agentic_proteins.memory` | `forwarding-only` | `bijux_proteomics_runtime.memory` | replace `agentic_proteins.memory` with `bijux_proteomics_runtime.memory` |
| `agentic_proteins.memory.schemas` | `forwarding-only` | `bijux_proteomics_runtime.memory.schemas` | replace `agentic_proteins.memory.schemas` with `bijux_proteomics_runtime.memory.schemas` |
| `agentic_proteins.memory.store` | `forwarding-only` | `bijux_proteomics_runtime.memory.store` | replace `agentic_proteins.memory.store` with `bijux_proteomics_runtime.memory.store` |
| `agentic_proteins.providers` | `forwarding-only` | `bijux_proteomics_runtime.providers` | replace `agentic_proteins.providers` with `bijux_proteomics_runtime.providers` |
| `agentic_proteins.providers.base` | `forwarding-only` | `bijux_proteomics_runtime.providers.base` | replace `agentic_proteins.providers.base` with `bijux_proteomics_runtime.providers.base` |
| `agentic_proteins.providers.errors` | `forwarding-only` | `bijux_proteomics_runtime.providers.errors` | replace `agentic_proteins.providers.errors` with `bijux_proteomics_runtime.providers.errors` |
| `agentic_proteins.providers.experimental` | `forwarding-only` | `bijux_proteomics_runtime.providers.experimental` | replace `agentic_proteins.providers.experimental` with `bijux_proteomics_runtime.providers.experimental` |
| `agentic_proteins.providers.experimental._async_utils` | `forwarding-only` | `bijux_proteomics_runtime.providers.experimental._async_utils` | replace `agentic_proteins.providers.experimental._async_utils` with `bijux_proteomics_runtime.providers.experimental._async_utils` |
| `agentic_proteins.providers.experimental.colabfold` | `forwarding-only` | `bijux_proteomics_runtime.providers.experimental.colabfold` | replace `agentic_proteins.providers.experimental.colabfold` with `bijux_proteomics_runtime.providers.experimental.colabfold` |
| `agentic_proteins.providers.experimental.openprotein` | `forwarding-only` | `bijux_proteomics_runtime.providers.experimental.openprotein` | replace `agentic_proteins.providers.experimental.openprotein` with `bijux_proteomics_runtime.providers.experimental.openprotein` |
| `agentic_proteins.providers.factory` | `forwarding-only` | `bijux_proteomics_runtime.providers.factory` | replace `agentic_proteins.providers.factory` with `bijux_proteomics_runtime.providers.factory` |
| `agentic_proteins.providers.heuristic` | `forwarding-only` | `bijux_proteomics_runtime.providers.heuristic` | replace `agentic_proteins.providers.heuristic` with `bijux_proteomics_runtime.providers.heuristic` |
| `agentic_proteins.providers.local` | `forwarding-only` | `bijux_proteomics_runtime.providers.local` | replace `agentic_proteins.providers.local` with `bijux_proteomics_runtime.providers.local` |
| `agentic_proteins.providers.local.esmfold` | `forwarding-only` | `bijux_proteomics_runtime.providers.local.esmfold` | replace `agentic_proteins.providers.local.esmfold` with `bijux_proteomics_runtime.providers.local.esmfold` |
| `agentic_proteins.providers.local.rosettafold` | `forwarding-only` | `bijux_proteomics_runtime.providers.local.rosettafold` | replace `agentic_proteins.providers.local.rosettafold` with `bijux_proteomics_runtime.providers.local.rosettafold` |
| `agentic_proteins.registry` | `forwarding-only` | `bijux_proteomics_runtime.registry` | replace `agentic_proteins.registry` with `bijux_proteomics_runtime.registry` |
| `agentic_proteins.registry.agents` | `forwarding-only` | `bijux_proteomics_runtime.registry.agents` | replace `agentic_proteins.registry.agents` with `bijux_proteomics_runtime.registry.agents` |
| `agentic_proteins.registry.tools` | `forwarding-only` | `bijux_proteomics_runtime.registry.tools` | replace `agentic_proteins.registry.tools` with `bijux_proteomics_runtime.registry.tools` |
| `agentic_proteins.report` | `forwarding-only` | `bijux_proteomics_intelligence.report` | replace `agentic_proteins.report` with `bijux_proteomics_intelligence.report` |
| `agentic_proteins.report.compute` | `forwarding-only` | `bijux_proteomics_intelligence.report.compute` | replace `agentic_proteins.report.compute` with `bijux_proteomics_intelligence.report.compute` |
| `agentic_proteins.report.model` | `forwarding-only` | `bijux_proteomics_intelligence.report.model` | replace `agentic_proteins.report.model` with `bijux_proteomics_intelligence.report.model` |
| `agentic_proteins.report.render` | `forwarding-only` | `bijux_proteomics_intelligence.report.render` | replace `agentic_proteins.report.render` with `bijux_proteomics_intelligence.report.render` |
| `agentic_proteins.runtime` | `forwarding-only` | `bijux_proteomics_runtime.runtime` | replace `agentic_proteins.runtime` with `bijux_proteomics_runtime.runtime` |
| `agentic_proteins.runtime.context` | `forwarding-only` | `bijux_proteomics_runtime.runtime.context` | replace `agentic_proteins.runtime.context` with `bijux_proteomics_runtime.runtime.context` |
| `agentic_proteins.runtime.context.context` | `forwarding-only` | `bijux_proteomics_runtime.runtime.context.context` | replace `agentic_proteins.runtime.context.context` with `bijux_proteomics_runtime.runtime.context.context` |
| `agentic_proteins.runtime.context.lifecycle` | `forwarding-only` | `bijux_proteomics_runtime.runtime.context.lifecycle` | replace `agentic_proteins.runtime.context.lifecycle` with `bijux_proteomics_runtime.runtime.context.lifecycle` |
| `agentic_proteins.runtime.context.output` | `forwarding-only` | `bijux_proteomics_runtime.runtime.context.output` | replace `agentic_proteins.runtime.context.output` with `bijux_proteomics_runtime.runtime.context.output` |
| `agentic_proteins.runtime.context.request` | `forwarding-only` | `bijux_proteomics_runtime.runtime.context.request` | replace `agentic_proteins.runtime.context.request` with `bijux_proteomics_runtime.runtime.context.request` |
| `agentic_proteins.runtime.control` | `forwarding-only` | `bijux_proteomics_runtime.runtime.control` | replace `agentic_proteins.runtime.control` with `bijux_proteomics_runtime.runtime.control` |
| `agentic_proteins.runtime.control.artifacts` | `forwarding-only` | `bijux_proteomics_runtime.runtime.control.artifacts` | replace `agentic_proteins.runtime.control.artifacts` with `bijux_proteomics_runtime.runtime.control.artifacts` |
| `agentic_proteins.runtime.control.execution` | `forwarding-only` | `bijux_proteomics_runtime.runtime.control.execution` | replace `agentic_proteins.runtime.control.execution` with `bijux_proteomics_runtime.runtime.control.execution` |
| `agentic_proteins.runtime.control.state_machine` | `forwarding-only` | `bijux_proteomics_runtime.runtime.control.state_machine` | replace `agentic_proteins.runtime.control.state_machine` with `bijux_proteomics_runtime.runtime.control.state_machine` |
| `agentic_proteins.runtime.infra` | `forwarding-only` | `bijux_proteomics_runtime.runtime.infra` | replace `agentic_proteins.runtime.infra` with `bijux_proteomics_runtime.runtime.infra` |
| `agentic_proteins.runtime.infra.analysis` | `forwarding-only` | `bijux_proteomics_runtime.runtime.infra.analysis` | replace `agentic_proteins.runtime.infra.analysis` with `bijux_proteomics_runtime.runtime.infra.analysis` |
| `agentic_proteins.runtime.infra.capabilities` | `forwarding-only` | `bijux_proteomics_runtime.runtime.infra.capabilities` | replace `agentic_proteins.runtime.infra.capabilities` with `bijux_proteomics_runtime.runtime.infra.capabilities` |
| `agentic_proteins.runtime.infra.config` | `forwarding-only` | `bijux_proteomics_runtime.runtime.infra.config` | replace `agentic_proteins.runtime.infra.config` with `bijux_proteomics_runtime.runtime.infra.config` |
| `agentic_proteins.runtime.infra.observability` | `forwarding-only` | `bijux_proteomics_runtime.runtime.infra.observability` | replace `agentic_proteins.runtime.infra.observability` with `bijux_proteomics_runtime.runtime.infra.observability` |
| `agentic_proteins.runtime.infra.reliability` | `forwarding-only` | `bijux_proteomics_runtime.runtime.infra.reliability` | replace `agentic_proteins.runtime.infra.reliability` with `bijux_proteomics_runtime.runtime.infra.reliability` |
| `agentic_proteins.runtime.infra.telemetry` | `forwarding-only` | `bijux_proteomics_runtime.runtime.infra.telemetry` | replace `agentic_proteins.runtime.infra.telemetry` with `bijux_proteomics_runtime.runtime.infra.telemetry` |
| `agentic_proteins.runtime.workspace` | `forwarding-only` | `bijux_proteomics_runtime.runtime.workspace` | replace `agentic_proteins.runtime.workspace` with `bijux_proteomics_runtime.runtime.workspace` |
| `agentic_proteins.sandbox` | `forwarding-only` | `bijux_proteomics_runtime.sandbox` | replace `agentic_proteins.sandbox` with `bijux_proteomics_runtime.sandbox` |
| `agentic_proteins.state` | `forwarding-only` | `bijux_proteomics_runtime.state` | replace `agentic_proteins.state` with `bijux_proteomics_runtime.state` |
| `agentic_proteins.state.schemas` | `forwarding-only` | `bijux_proteomics_runtime.state.schemas` | replace `agentic_proteins.state.schemas` with `bijux_proteomics_runtime.state.schemas` |
| `agentic_proteins.state.snapshot` | `forwarding-only` | `bijux_proteomics_runtime.state.snapshot` | replace `agentic_proteins.state.snapshot` with `bijux_proteomics_runtime.state.snapshot` |
| `agentic_proteins.tools` | `forwarding-only` | `bijux_proteomics_runtime.tools` | replace `agentic_proteins.tools` with `bijux_proteomics_runtime.tools` |
| `agentic_proteins.tools.base` | `forwarding-only` | `bijux_proteomics_runtime.tools.base` | replace `agentic_proteins.tools.base` with `bijux_proteomics_runtime.tools.base` |
| `agentic_proteins.tools.heuristic` | `forwarding-only` | `bijux_proteomics_runtime.tools.heuristic` | replace `agentic_proteins.tools.heuristic` with `bijux_proteomics_runtime.tools.heuristic` |
| `agentic_proteins.tools.schemas` | `forwarding-only` | `bijux_proteomics_runtime.tools.schemas` | replace `agentic_proteins.tools.schemas` with `bijux_proteomics_runtime.tools.schemas` |
| `agentic_proteins.validation` | `forwarding-only` | `bijux_proteomics_runtime.validation` | replace `agentic_proteins.validation` with `bijux_proteomics_runtime.validation` |
| `agentic_proteins.validation.agents` | `forwarding-only` | `bijux_proteomics_runtime.validation.agents` | replace `agentic_proteins.validation.agents` with `bijux_proteomics_runtime.validation.agents` |
| `agentic_proteins.validation.state` | `forwarding-only` | `bijux_proteomics_runtime.validation.state` | replace `agentic_proteins.validation.state` with `bijux_proteomics_runtime.validation.state` |
| `agentic_proteins.validation.tools` | `forwarding-only` | `bijux_proteomics_runtime.validation.tools` | replace `agentic_proteins.validation.tools` with `bijux_proteomics_runtime.validation.tools` |

## Reading The Guide

- `forwarding-only` means the compatibility module is a narrow bridge and callers should move directly to the named canonical target.
- `review-required` means the module is still intentionally broader and needs explicit migration review before callers are switched.
- this document should be regenerated whenever compatibility forwarding changes so release and retirement discussions are based on current code rather than memory.
