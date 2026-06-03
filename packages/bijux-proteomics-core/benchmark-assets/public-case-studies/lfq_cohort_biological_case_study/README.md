# LFQ cohort biological case study

This case study turns the tracked LFQ cohort public package into one bounded
end-to-end biological interpretation workflow.

Public data and sample metadata come directly from:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale_ms1_features.tsv`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/evidence/study_scale.design.tsv`

This case-study root adds only the interpretation-side support needed to finish
the workflow inside the repository:

- `biology/reference.fasta`
- `biology/annotations.tsv`
- `biology/go_annotations.tsv`
- `biology/pathway_memberships.tsv`
- `biology/complex_memberships.tsv`

Why the case study exists:

- prove that one tracked public LFQ snapshot can run through differential
  protein reporting, QC, enrichment, and final biological report export
- keep the exploratory interpretation policy explicit instead of implying
  decision-grade certainty from a tiny bundled cohort snapshot
- anchor the final biology proof to inspectable files rather than private
  setup knowledge

What the case study does not claim:

- that this bundled snapshot is a full rerun of the upstream public study
- that the exploratory enrichment thresholds are decision-grade
- that three-protein bundled evidence transfers to broad cohort conclusions
