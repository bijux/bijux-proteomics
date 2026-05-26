# Shipped Demo CLI Tutorial

This walkthrough shows one minimal non-developer CLI path through the shipped
core demo. It covers four things only:

- run the local shipped demo
- understand the top-level output layout
- validate the governed result bundle
- query one result object without knowing the internal report paths

The commands below assume the `bijux-proteomics` CLI is available in the
current environment.

## 1. Run the shipped demo

```bash
bijux-proteomics demo --out-dir demo_result
```

The demo writes a compact but real reviewable output root. The most important
artifacts are:

- `demo_result/surprising_demo_report.json` for the top-level demo run record
- `demo_result/biological_review/` for governed protein and pathway review outputs
- `demo_result/biological_review/biological_report.html` for the governed biological review report
- `demo_result/ptm_review/` for governed PTM review outputs

## 2. Validate the governed result bundle

```bash
bijux-proteomics validate-result demo_result --manifest-json-out demo_result/result_manifest.json --summary-tsv-out demo_result/result_validation.summary.tsv --warning-tsv-out demo_result/result_validation.warnings.tsv --out demo_result/result_validation.json
```

This step validates the result root as one governed package instead of treating
the nested report directories as ad hoc files. The command emits:

- `demo_result/result_manifest.json` as the governed manifest over the demo result
- `demo_result/result_validation.summary.tsv` as a compact validation summary
- `demo_result/result_validation.warnings.tsv` for non-fatal caveats
- `demo_result/result_validation.json` for the machine-readable validation report

## 3. Query one result object

```bash
bijux-proteomics query-result demo_result --query P11111:S5:Phospho --summary-tsv-out demo_result/query_result.summary.tsv --hit-tsv-out demo_result/query_result.hits.tsv --out demo_result/query_result.json
```

This query searches the governed result root directly. It does not require you
to know whether the relevant object lives in `biological_review/` or
`ptm_review/`.

The command emits:

- `demo_result/query_result.summary.tsv` with index and hit counts
- `demo_result/query_result.hits.tsv` with the matching object rows
- `demo_result/query_result.json` with the complete machine-readable query report

## What this proves

- the shipped demo is runnable from one core-owned CLI command
- the output root has one stable top-level layout
- the result root can be validated into one governed manifest
- one protein/PTM object can be queried from the result root without private path knowledge
