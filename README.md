# PAM50 vs IHC Surrogate: Information Ceiling Study

**Routine clinicopathological data cannot reliably reproduce 4-class PAM50 intrinsic subtypes in breast cancer: a multicohort in silico study defining the luminal grey zone**

Rafael de Negreiros Botan¹,*, Sandro José Martins³, João Batista de Sousa¹,²

¹ University of Brasília, Brasília, Brazil, Medical Sciences Postgraduate Program, School of Medicine, DF, Brazil  
² University of Brasília, Brasília, Brazil, Department of Colorectal Surgery, Hospital Universitário de Brasília, Brasília, Brazil  
³ University of Brasília, Brasília, Brazil, Department of Oncology, Hospital Universitário de Brasília, Brasília, Brazil  
\* Corresponding author: oncologista@gmail.com

## Overview

This repository contains all code, processed data, and figures for the study evaluating whether machine-learning models trained on routine immunohistochemistry (IHC) variables can approximate PAM50 intrinsic breast cancer subtypes.

**Key finding:** Routine clinicopathological variables impose an information ceiling for 4-class PAM50 reconstruction. In external matched comparisons, machine-learning models did not outperform the conventional IHC surrogate, and the residual uncertainty concentrated at the Luminal A/Luminal B boundary.

## Cohorts

| Cohort | n | Platform | Role |
|--------|---|----------|------|
| GSE81538 | 383 | SCAN-B RNA-seq | Development |
| GSE96058 | 2,867 | SCAN-B RNA-seq | Development |
| TCGA-BRCA | 519 | RNA-seq | External validation |
| METABRIC | 1,608 | Microarray | External validation |

**Total: 5,377 tumours with 4-class PAM50 labels**

## Repository structure

```
├── scripts/
│   ├── 01_download_data.py       # Download raw data from GEO/cBioPortal
│   ├── 02_parse_and_harmonize.py # Parse and harmonise across cohorts
│   ├── 03_full_analysis.py       # Main ML analysis + bootstrap CIs
│   ├── 05_enhanced_analysis.py   # Grey-zone + sensitivity analyses
│   ├── 07_figures_R.R            # Publication figures (R/ggplot2; retained for provenance)
│   ├── 11_bcrt_word.py           # Generate BCRT Word manuscript
│   └── 13_fix_bcrt_figures.py    # Regenerate final BCRT figures when local R rendering is unavailable
├── data/
│   └── processed/                # Harmonised datasets (tracked)
├── tables/                       # Result tables (CSV)
├── figures/                      # Python-generated analysis figures (PNG)
├── figures_R/                    # Final publication figures (PNG + PDF)
├── manuscript/                   # Word documents for submission
│   ├── manuscript_BCRT_v1.md
│   ├── manuscript_BCRT_v1.docx
│   ├── tables_BCRT.docx
│   └── Manuscript_BCRT_AllText_Tables_Figures.docx
└── requirements.txt
```

## Reproducing the analysis

### Prerequisites

- Python 3.10+
- R 4.3+ with packages: `ggplot2`, `patchwork`, `scales`, `RColorBrewer`, `dplyr`, `tidyr`

### Steps

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Download raw data (~25 MB)
python scripts/01_download_data.py

# 3. Parse and harmonise
python scripts/02_parse_and_harmonize.py

# 4. Run main analysis (ML models + bootstrap CIs)
python scripts/03_full_analysis.py

# 5. Enhanced analyses (grey zone, sensitivity)
python scripts/05_enhanced_analysis.py

# 6. Generate final BCRT publication figures
python scripts/13_fix_bcrt_figures.py

# 7. Generate Word manuscript
python scripts/11_bcrt_word.py
```

Administrative submission materials, reviewer suggestions, cover letters, and local package-builder scripts are not included in this public repository.

## Key results

- **IHC surrogate macro-F1:** 0.644 (95% CI 0.616–0.669) in the METABRIC receptor-grade matched subset
- **Best ML model (XGBoost + grade):** 0.559 (0.533–0.584), paired delta versus surrogate −0.085
- **Luminal A→B crossover:** 42.5% of molecular LumB received LumA-like label
- **Grey zone:** 13.5% of cases with <50% confidence, 73.6% luminal, only 15.9% ML accuracy
- **3-class collapse:** macro-F1 rises to 0.767, confirming luminal boundary as bottleneck

## Data sources

- **GSE81538, GSE96058:** [NCBI GEO](https://www.ncbi.nlm.nih.gov/geo/)
- **TCGA-BRCA, METABRIC:** [cBioPortal](https://www.cbioportal.org/)

## License

This work is provided for academic and research purposes. All source data are publicly available under their respective licenses.
