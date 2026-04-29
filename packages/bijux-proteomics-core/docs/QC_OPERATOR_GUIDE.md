# QC Operator Guide

This guide explains how to turn normalized spectra, search results, FASTA
context, and optional design metadata into operator-facing QC artifacts.

## Command surface

```bash
bijux-proteomics qc report spectra.mgf results.tsv proteins.fasta \
  --design design.tsv \
  --policy qc_policy.json \
  --out qc.report.json \
  --tsv-out qc.metrics.tsv \
  --html-out qc.report.html \
  --manifest-out qc.evidence.json \
  --benchmark-out qc.benchmark.json
```

The command emits a JSON payload to stdout or `--out` and can also materialize:

- `qc.metrics.tsv` with one row per metric assessment
- `qc.report.html` for human review
- `qc.evidence.json` with input hashes, threshold policy, and generated artifact hashes
- `qc.benchmark.json` with execution timing snapshots for the report build

## Inputs

- `spectra.mgf`: parsed spectra used for spectrum count, TIC, precursor, and RT summaries
- `results.tsv`: normalized or mappable PSM table used for identification-rate,
  mass-error, charge-state, digestion-specificity, and contaminant summaries
- `proteins.fasta`: FASTA context used for peptide-to-protein reasoning and
  digestion specificity
- `design.tsv`: optional sample metadata including condition, replicate, and batch
- `qc_policy.json`: optional threshold file that overrides the built-in default policy

## Threshold policy model

Threshold policies are JSON-serializable and loaded into `QcThresholdPolicy`.
Each rule targets one metric key and can define warning and failure bounds.

Current policy behavior is explicit:

- `advisory` rules produce warnings or failures without blocking the run
- `enforced` rules produce warnings or failures and can mark the run or batch as blocked

This means the same metric can be important in two different ways:

- advisory: tells an operator something degraded and needs review
- enforced: tells an operator the run should not continue without intervention

## Interpreting a good run

A good run usually shows:

- spectrum count close to the batch median or expected instrument regime
- identification rate above the warning threshold
- precursor mass error centered near zero with narrow spread
- broad retention-time coverage rather than a short collapsed window
- expected charge-state distribution for the acquisition method
- low contaminant burden
- mostly enzymatic digestion specificity for tryptic workflows

In the HTML and TSV outputs, that normally appears as mostly `pass` assessments,
with zero or few `warn` entries and no enforced failures.

## Interpreting a bad run

Bad runs usually cluster in one of a few patterns:

1. Acquisition failure:
   low spectrum count, narrow RT coverage, weak or absent identifications.
2. Search/result quality failure:
   reasonable spectra volume but low identification rate, poor score/q-value shape,
   or unexpectedly high contaminant burden.
3. Calibration/drift failure:
   elevated mass error with otherwise normal acquisition volume.
4. Sample-prep/digestion failure:
   high missed-cleavage rate or degraded digestion specificity.

When a run is blocked, inspect the `run_assessment["blocked"]` flag and then
look at the metrics with `disposition="fail"` and `severity="enforced"`.

## Diagnose a failed run

Start with this sequence:

1. Open `qc.report.json` and find blocked metrics.
2. Confirm the exact input set in `qc.evidence.json`.
3. Review `qc.metrics.tsv` for all warned and failed metrics in one sortable table.
4. Compare the run against the batch section if batch metadata was supplied.
5. Check `qc.benchmark.json` only if report generation itself looks anomalous.

Typical next actions:

- low spectrum count: inspect raw acquisition and injection quality
- high precursor error: inspect calibration and mass-drift behavior
- low identification rate: inspect search settings, enzyme specificity, and contaminant burden
- high missed-cleavage rate: inspect digestion conditions and protease choice
- blocked contaminants: inspect sample handling and cleanup

## Evidence and reproducibility

`qc.evidence.json` binds the QC decision to:

- hashes of input files
- the applied threshold policy
- hashes of generated QC artifacts
- run and batch identifiers when available

That manifest is the operator-facing anchor for proving what exact evidence the
QC decision came from.

## Current boundaries

This workflow now covers thresholded QC assessment, operator-friendly report
materialization, evidence capture, and performance snapshots. It does not yet
provide:

- interactive dashboards
- vendor-specific calibration heuristics
- longitudinal fleet-wide QC trending
- auto-remediation or workflow stopping outside the returned blocked status
