# Advanced DIA-NN Python API

This tutorial shows the minimal non-CLI library path for one advanced DIA-NN
run:

1. build an `AdvancedDiannWorkflowConfig`
2. execute the resumable runtime workflow
3. archive the completed run into `result_manifest.json`
4. rehydrate the completed run through runtime
5. query one archived protein result

The example below uses the shipped advanced DIA-NN fixture files from this
repository. Replace those three input paths with your own DIA-NN result TSV,
experimental design TSV, and FASTA when you run the same path on real data.

```python
from pathlib import Path

from bijux_proteomics.workflow import AdvancedDiannWorkflowConfig
from bijux_proteomics_runtime.rehydrate import load_completed_run
from bijux_proteomics_runtime.workflows import (
    AdvancedDiannRuntimeStatus,
    archive_completed_advanced_diann_run,
    run_resumable_advanced_diann_workflow,
)

try:
    repo_root = REPO_ROOT
    output_root = TMP_PATH
except NameError:
    repo_root = Path.cwd()
    output_root = repo_root / "artifacts"

fixture_root = (
    repo_root
    / "packages"
    / "bijux-proteomics-core"
    / "tests"
    / "fixtures"
    / "workflow"
)
output_dir = output_root / "advanced_diann_python_api"

config = AdvancedDiannWorkflowConfig(
    result_tsv_path=fixture_root / "diann_advanced_report.tsv",
    design_tsv_path=fixture_root / "diann_biological.design.tsv",
    proteins_fasta_path=fixture_root / "diann_advanced_reference.fasta",
    output_dir=output_dir,
    condition_a="control",
    condition_b="treatment",
)

runtime_report = run_resumable_advanced_diann_workflow(config)
archive_report = archive_completed_advanced_diann_run(
    config,
    runtime_report=runtime_report,
)
study_result = load_completed_run(output_dir)
protein = study_result.query_archived_protein(
    representative_protein_ref="O14920"
)

assert runtime_report.status is AdvancedDiannRuntimeStatus.COMPLETED
assert archive_report.archive_validated is True
assert protein.object_id == "protein:PG003"
assert protein.representative_protein_ref == "O14920"
assert protein.evidence_tier is not None
```

After the archive step, the output directory contains:

- `result_manifest.json` for governed archive rehydration
- `advanced_diann_completed_run_report.json` for the runtime-owned archive proof
- the workflow-owned advanced DIA-NN biological and review artifacts that back
  the archived result query surface
