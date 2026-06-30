# SPDX-License-Identifier: Apache-2.0
# Copyright © 2026 Bijan Mousavi

"""Dispatch entry points for study-result builders."""

from __future__ import annotations

from bijux_proteomics.domain.errors import InvalidWorkflowError
from bijux_proteomics.workflow.pipelines.advanced_diann import (
    AdvancedDiannWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_fragpipe import (
    AdvancedFragpipeWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_maxquant import (
    AdvancedMaxquantWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_ptm import AdvancedPtmWorkflowReport
from bijux_proteomics.workflow.pipelines.advanced_targeted import (
    TargetedValidationWorkflowReport,
)
from bijux_proteomics.workflow.pipelines.advanced_tmt import AdvancedTmtWorkflowReport
from bijux_proteomics.workflow.pipelines.dda_biological_workflow import (
    DdaBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.diann_biological_workflow import (
    DiannBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.flagship_run import ProteomicsRunBundle
from bijux_proteomics.workflow.pipelines.maxquant_biological_workflow import (
    MaxquantBiologicalWorkflowBundle,
)
from bijux_proteomics.workflow.pipelines.ptm_site_workflow import PtmSiteWorkflowBundle
from bijux_proteomics.workflow.pipelines.tmt_experiment_workflow import (
    TmtExperimentWorkflowBundle,
)
from bijux_proteomics.workflow.reports.biological_reporting import (
    BiologicalResultReportBundle,
)
from bijux_proteomics.workflow.studies.study_results.advanced import (
    build_proteomics_study_result_from_advanced_diann_workflow_report,
    build_proteomics_study_result_from_advanced_fragpipe_workflow_report,
    build_proteomics_study_result_from_advanced_maxquant_workflow_report,
    build_proteomics_study_result_from_advanced_ptm_workflow_report,
    build_proteomics_study_result_from_advanced_tmt_workflow_report,
)
from bijux_proteomics.workflow.studies.study_results.label_free import (
    build_proteomics_study_result_from_biological_report_bundle,
    build_proteomics_study_result_from_dda_workflow_bundle,
    build_proteomics_study_result_from_diann_workflow_bundle,
    build_proteomics_study_result_from_maxquant_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.models import ProteomicsStudyResult
from bijux_proteomics.workflow.studies.study_results.modification import (
    build_proteomics_study_result_from_ptm_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.multiplex import (
    build_proteomics_study_result_from_tmt_workflow_bundle,
)
from bijux_proteomics.workflow.studies.study_results.validation import (
    build_proteomics_study_result_from_targeted_validation_workflow_report,
)


def build_proteomics_study_result(
    source: (
        AdvancedDiannWorkflowReport
        | AdvancedFragpipeWorkflowReport
        | AdvancedMaxquantWorkflowReport
        | AdvancedPtmWorkflowReport
        | AdvancedTmtWorkflowReport
        | BiologicalResultReportBundle
        | DdaBiologicalWorkflowBundle
        | DiannBiologicalWorkflowBundle
        | MaxquantBiologicalWorkflowBundle
        | ProteomicsRunBundle
        | PtmSiteWorkflowBundle
        | TargetedValidationWorkflowReport
        | TmtExperimentWorkflowBundle
    ),
) -> ProteomicsStudyResult:
    """Normalize one owned workflow output into a comparable study result."""

    if isinstance(source, ProteomicsRunBundle):
        return build_proteomics_study_result_from_run_bundle(source)
    if isinstance(source, AdvancedDiannWorkflowReport):
        return build_proteomics_study_result_from_advanced_diann_workflow_report(source)
    if isinstance(source, AdvancedFragpipeWorkflowReport):
        return build_proteomics_study_result_from_advanced_fragpipe_workflow_report(
            source
        )
    if isinstance(source, AdvancedMaxquantWorkflowReport):
        return build_proteomics_study_result_from_advanced_maxquant_workflow_report(
            source
        )
    if isinstance(source, AdvancedPtmWorkflowReport):
        return build_proteomics_study_result_from_advanced_ptm_workflow_report(source)
    if isinstance(source, AdvancedTmtWorkflowReport):
        return build_proteomics_study_result_from_advanced_tmt_workflow_report(source)
    if isinstance(source, DdaBiologicalWorkflowBundle):
        return build_proteomics_study_result_from_dda_workflow_bundle(source)
    if isinstance(source, DiannBiologicalWorkflowBundle):
        return build_proteomics_study_result_from_diann_workflow_bundle(source)
    if isinstance(source, MaxquantBiologicalWorkflowBundle):
        return build_proteomics_study_result_from_maxquant_workflow_bundle(source)
    if isinstance(source, TargetedValidationWorkflowReport):
        return build_proteomics_study_result_from_targeted_validation_workflow_report(
            source
        )
    if isinstance(source, TmtExperimentWorkflowBundle):
        return build_proteomics_study_result_from_tmt_workflow_bundle(source)
    if isinstance(source, PtmSiteWorkflowBundle):
        return build_proteomics_study_result_from_ptm_workflow_bundle(source)
    if isinstance(source, BiologicalResultReportBundle):
        return build_proteomics_study_result_from_biological_report_bundle(source)
    raise TypeError(f"unsupported proteomics study result source: {type(source)!r}")


def build_proteomics_study_result_from_run_bundle(
    bundle: ProteomicsRunBundle,
) -> ProteomicsStudyResult:
    """Normalize one flagship run bundle into a study-level comparison object."""

    if bundle.diann_workflow is not None:
        return build_proteomics_study_result_from_diann_workflow_bundle(
            bundle.diann_workflow
        )
    if bundle.maxquant_workflow is not None:
        return build_proteomics_study_result_from_maxquant_workflow_bundle(
            bundle.maxquant_workflow
        )
    if bundle.fragpipe_workflow is not None:
        return build_proteomics_study_result_from_dda_workflow_bundle(
            bundle.fragpipe_workflow
        )
    raise InvalidWorkflowError(
        "proteomics run bundle does not include a study workflow payload"
    )


__all__ = [
    "build_proteomics_study_result",
    "build_proteomics_study_result_from_run_bundle",
]
