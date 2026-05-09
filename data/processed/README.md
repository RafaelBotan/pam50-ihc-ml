# Processed Data Files

Processed data files are derived from public source cohorts and contain harmonised variables used in the analyses.

- `harmonized_full.csv`: final harmonised analysis dataset with PAM50 labels and routine clinicopathological variables.
- `cohort_harmonized.csv`: intermediate harmonised clinical dataset retained for provenance.
- `cohort_summary.csv`: cohort-level summary generated during harmonisation.
- `GSE81538_metadata.csv`: processed SCAN-B metadata used during harmonisation.

Raw downloaded files are not tracked. They can be regenerated with `python scripts/01_download_data.py`.
