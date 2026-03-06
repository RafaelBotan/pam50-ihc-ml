"""
Phase 2-3: Parse raw data and harmonize all cohorts into a unified format.
Produces: data/processed/cohort_harmonized.csv
"""

import os
import sys
import re
import requests
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")


# ============================================================
# 1. Parse GSE81538 (rich multi-observer IHC + PAM50)
# ============================================================

def parse_gse81538():
    print("=== Parsing GSE81538 ===")
    filepath = os.path.join(RAW_DIR, "GSE81538_series_matrix.txt")

    metadata = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith('!Sample_geo_accession'):
                vals = line.split('\t')[1:]
                metadata['sample_id'] = [v.strip('"') for v in vals]
            elif line.startswith('!Sample_characteristics_ch1'):
                vals = line.split('\t')[1:]
                vals = [v.strip('"') for v in vals]
                if vals:
                    key_part = vals[0].split(':')[0].strip() if ':' in vals[0] else 'unknown'
                    parsed = [v.split(':', 1)[1].strip() if ':' in v else v for v in vals]
                    if key_part not in metadata:
                        metadata[key_part] = parsed
                    else:
                        # Duplicate key - append number
                        i = 2
                        while f"{key_part}_{i}" in metadata:
                            i += 1
                        metadata[f"{key_part}_{i}"] = parsed

    df = pd.DataFrame(metadata)
    n_samples = len(df)
    print(f"  Raw parsed: {df.shape}")
    print(f"  Columns: {list(df.columns)}")

    # Convert numeric columns
    for col in df.columns:
        if col in ['sample_id', 'tissue', 'pam50 subtype']:
            continue
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        except:
            pass

    # Build harmonized dataframe
    harm = pd.DataFrame()
    harm['sample_id'] = df['sample_id']
    harm['cohort'] = 'GSE81538'
    harm['platform'] = 'RNA-seq'

    # PAM50
    harm['pam50_label'] = df['pam50 subtype']
    harm['pam50_source'] = 'published'

    # ER consensus (0-3 scale in this dataset)
    if 'er consensus' in df.columns:
        harm['er_score'] = df['er consensus']
        harm['er_status'] = (df['er consensus'] > 0).map({True: 'Positive', False: 'Negative'})

    # PgR consensus
    if 'pgr consensus' in df.columns:
        harm['pr_score'] = df['pgr consensus']
        harm['pr_status'] = (df['pgr consensus'] > 0).map({True: 'Positive', False: 'Negative'})

    # HER2 IHC clinical reading
    if 'her2 ihc clinreading' in df.columns:
        harm['her2_ihc_score'] = df['her2 ihc clinreading']

    # HER2 clinical status (0/1)
    if 'her2 clinical status' in df.columns:
        harm['her2_status'] = df['her2 clinical status'].map({0: 'Negative', 1: 'Positive'})

    # HER2 consensus
    if 'her2 consensus' in df.columns:
        harm['her2_consensus'] = df['her2 consensus']

    # Ki67 consensus
    if 'ki67 consensus' in df.columns:
        harm['ki67'] = df['ki67 consensus']

    # NHG consensus (grade)
    if 'nhg consensus' in df.columns:
        harm['grade'] = df['nhg consensus']

    print(f"  Harmonized: {harm.shape}")
    print(f"  PAM50 distribution: {harm['pam50_label'].value_counts().to_dict()}")
    print(f"  ER status: {harm['er_status'].value_counts().to_dict()}")
    print(f"  Missing Ki67: {harm['ki67'].isna().sum()}")
    print(f"  Missing grade: {harm['grade'].isna().sum()}")

    return harm


# ============================================================
# 2. Parse GSE96058 (needs re-download or alternative parsing)
# ============================================================

def download_and_parse_gse96058():
    print("\n=== Parsing GSE96058 ===")

    # GSE96058 is large - try to get supplementary clinical file
    # The series matrix may be split or unavailable
    # Try the GEO2R approach - download the clinical annotation directly

    proc_file = os.path.join(PROC_DIR, "GSE96058_metadata.csv")

    # Try downloading from supplementary files
    supp_url = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE96nnn/GSE96058/suppl/"
    matrix_urls = [
        "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE96nnn/GSE96058/matrix/GSE96058-GPL11154_series_matrix.txt.gz",
        "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE96nnn/GSE96058/matrix/GSE96058-GPL23108_series_matrix.txt.gz",
    ]

    all_dfs = []
    for url in matrix_urls:
        cache_file = os.path.join(RAW_DIR, os.path.basename(url).replace('.gz', ''))
        if not os.path.exists(cache_file):
            print(f"  Downloading {os.path.basename(url)}...")
            try:
                import gzip
                r = requests.get(url, timeout=300)
                if r.status_code == 200:
                    content = gzip.decompress(r.content).decode('utf-8', errors='replace')
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"    -> OK ({len(content)} chars)")
                else:
                    print(f"    -> Failed: {r.status_code}")
                    continue
            except Exception as e:
                print(f"    -> Error: {e}")
                continue

        # Parse
        metadata = {}
        with open(cache_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('!Sample_geo_accession'):
                    vals = line.split('\t')[1:]
                    metadata['sample_id'] = [v.strip('"') for v in vals]
                elif line.startswith('!Sample_characteristics_ch1'):
                    vals = line.split('\t')[1:]
                    vals = [v.strip('"') for v in vals]
                    if vals:
                        key_part = vals[0].split(':')[0].strip() if ':' in vals[0] else 'unknown'
                        parsed = [v.split(':', 1)[1].strip() if ':' in v else v for v in vals]
                        if key_part not in metadata:
                            metadata[key_part] = parsed
                        else:
                            i = 2
                            while f"{key_part}_{i}" in metadata:
                                i += 1
                            metadata[f"{key_part}_{i}"] = parsed

        if 'sample_id' in metadata:
            sub_df = pd.DataFrame(metadata)
            print(f"  Parsed {os.path.basename(url)}: {sub_df.shape}, cols: {list(sub_df.columns)[:15]}")
            all_dfs.append(sub_df)

    if not all_dfs:
        print("  WARNING: Could not parse GSE96058")
        return pd.DataFrame()

    df = pd.concat(all_dfs, ignore_index=True)
    print(f"  Combined: {df.shape}")
    print(f"  Columns: {list(df.columns)}")

    # Convert numeric
    for col in df.columns:
        if col in ['sample_id', 'tissue', 'pam50 subtype', 'er', 'pgr', 'her2', 'ki67 status']:
            continue
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        except:
            pass

    # Build harmonized
    harm = pd.DataFrame()
    harm['sample_id'] = df['sample_id']
    harm['cohort'] = 'GSE96058'
    harm['platform'] = 'RNA-seq'

    # Try to map known column names
    col_lower = {c.lower(): c for c in df.columns}

    # PAM50
    for k in ['pam50 subtype', 'pam50', 'pam50subtype']:
        if k in col_lower:
            harm['pam50_label'] = df[col_lower[k]]
            harm['pam50_source'] = 'published'
            break

    # ER
    for k in ['er', 'er status', 'er_status']:
        if k in col_lower:
            vals = df[col_lower[k]]
            if vals.dtype == object:
                harm['er_status'] = vals.map(lambda x: 'Positive' if str(x).lower() in ['positive', 'pos', '1', '+'] else ('Negative' if str(x).lower() in ['negative', 'neg', '0', '-'] else x))
            else:
                harm['er_score'] = vals
                harm['er_status'] = vals.apply(lambda x: 'Positive' if x > 0 else 'Negative' if pd.notna(x) else np.nan)
            break

    # PgR
    for k in ['pgr', 'pr', 'pgr status', 'pr status']:
        if k in col_lower:
            vals = df[col_lower[k]]
            if vals.dtype == object:
                harm['pr_status'] = vals.map(lambda x: 'Positive' if str(x).lower() in ['positive', 'pos', '1', '+'] else ('Negative' if str(x).lower() in ['negative', 'neg', '0', '-'] else x))
            else:
                harm['pr_score'] = vals
                harm['pr_status'] = vals.apply(lambda x: 'Positive' if x > 0 else 'Negative' if pd.notna(x) else np.nan)
            break

    # HER2
    for k in ['her2', 'her2 status', 'her2_status']:
        if k in col_lower:
            vals = df[col_lower[k]]
            if vals.dtype == object:
                harm['her2_status'] = vals.map(lambda x: 'Positive' if str(x).lower() in ['positive', 'pos', '1', '+', 'amplified'] else ('Negative' if str(x).lower() in ['negative', 'neg', '0', '-', 'not amplified'] else x))
            else:
                harm['her2_status'] = vals.map({0: 'Negative', 1: 'Positive'})
            break

    # Ki67
    for k in ['ki67', 'ki67 status']:
        if k in col_lower:
            vals = df[col_lower[k]]
            if vals.dtype == object:
                # Try to extract numeric or categorical
                harm['ki67_status'] = vals
            else:
                harm['ki67'] = vals
            break

    # Grade / NHG
    for k in ['nhg', 'grade', 'nhg consensus']:
        if k in col_lower:
            harm['grade'] = pd.to_numeric(df[col_lower[k]], errors='coerce')
            break

    print(f"  Harmonized: {harm.shape}")
    if 'pam50_label' in harm.columns:
        print(f"  PAM50: {harm['pam50_label'].value_counts().to_dict()}")

    return harm


# ============================================================
# 3. Parse TCGA-BRCA
# ============================================================

def parse_tcga():
    print("\n=== Parsing TCGA-BRCA ===")
    df = pd.read_csv(os.path.join(RAW_DIR, "brca_tcga_clinical.tsv"), sep='\t')
    print(f"  Raw: {df.shape}")

    # Need to get PAM50 labels - try from cBioPortal molecular subtype
    # TCGA PAM50 labels are in the TCGA publication supplementary data
    # Try to get from cBioPortal API

    # Check if SUBTYPE column exists
    subtype_col = None
    for col in df.columns:
        if 'SUBTYPE' in col.upper() and 'HISTOL' not in col.upper():
            print(f"  Found subtype column: {col} -> {df[col].value_counts().head().to_dict()}")
            subtype_col = col

    # Try to fetch PAM50 from cBioPortal
    pam50_map = fetch_tcga_pam50()

    harm = pd.DataFrame()
    harm['sample_id'] = df['sampleId']
    harm['patient_id'] = df['patientId']
    harm['cohort'] = 'TCGA-BRCA'
    harm['platform'] = 'RNA-seq'

    # PAM50 from supplementary/cBioPortal
    if pam50_map is not None:
        harm = harm.merge(pam50_map, on='patient_id', how='left')
        print(f"  PAM50 mapped: {harm['pam50_label'].value_counts().to_dict()}")
    else:
        harm['pam50_label'] = np.nan
    harm['pam50_source'] = 'TCGA_publication'

    # ER
    harm['er_status'] = df['ER_STATUS_BY_IHC'].replace({'[Not Evaluated]': np.nan, 'Indeterminate': np.nan})
    if 'ER_STATUS_IHC_PERCENT_POSITIVE' in df.columns:
        harm['er_pct'] = pd.to_numeric(df['ER_STATUS_IHC_PERCENT_POSITIVE'], errors='coerce')

    # PR
    harm['pr_status'] = df['PR_STATUS_BY_IHC'].replace({'[Not Evaluated]': np.nan, 'Indeterminate': np.nan})
    if 'PR_STATUS_IHC_PERCENT_POSITIVE' in df.columns:
        harm['pr_pct'] = pd.to_numeric(df['PR_STATUS_IHC_PERCENT_POSITIVE'], errors='coerce')

    # HER2
    harm['her2_status'] = df['IHC_HER2'].replace({
        'Negative': 'Negative', 'Positive': 'Positive',
        'Equivocal': np.nan, 'Indeterminate': np.nan,
        '[Not Evaluated]': np.nan, '[Not Available]': np.nan
    })
    if 'HER2_IHC_SCORE' in df.columns:
        harm['her2_ihc_score'] = pd.to_numeric(df['HER2_IHC_SCORE'], errors='coerce')
    if 'HER2_FISH_STATUS' in df.columns:
        fish = df['HER2_FISH_STATUS'].replace({
            '[Not Evaluated]': np.nan, 'Indeterminate': np.nan, 'Equivocal': np.nan
        })
        harm['her2_fish'] = fish
        # For equivocal IHC cases, use FISH if available
        mask_equivocal = df['IHC_HER2'] == 'Equivocal'
        harm.loc[mask_equivocal & (fish == 'Positive'), 'her2_status'] = 'Positive'
        harm.loc[mask_equivocal & (fish == 'Negative'), 'her2_status'] = 'Negative'

    # Grade - TCGA doesn't have standard NHG but has HISTOLOGICAL_GRADE
    for gcol in ['HISTOLOGICAL_GRADE', 'NEOPLASM_HISTOLOGIC_GRADE', 'GRADE']:
        if gcol in df.columns:
            harm['grade'] = pd.to_numeric(df[gcol].replace({
                '[Not Available]': np.nan, '[Not Evaluated]': np.nan
            }), errors='coerce')
            break

    # Age
    if 'AGE' in df.columns:
        harm['age'] = pd.to_numeric(df['AGE'], errors='coerce')

    # Stage
    if 'AJCC_PATHOLOGIC_TUMOR_STAGE' in df.columns:
        harm['stage'] = df['AJCC_PATHOLOGIC_TUMOR_STAGE']

    # Tumor size
    if 'AJCC_TUMOR_PATHOLOGIC_PT' in df.columns:
        harm['tumor_t'] = df['AJCC_TUMOR_PATHOLOGIC_PT']

    # Nodes
    if 'AJCC_NODES_PATHOLOGIC_PN' in df.columns:
        harm['node_n'] = df['AJCC_NODES_PATHOLOGIC_PN']

    # Histology
    if 'HISTOLOGICAL_SUBTYPE' in df.columns:
        harm['histology'] = df['HISTOLOGICAL_SUBTYPE']
    elif 'CANCER_TYPE_DETAILED' in df.columns:
        harm['histology'] = df['CANCER_TYPE_DETAILED']

    print(f"  Harmonized: {harm.shape}")
    print(f"  ER status: {harm['er_status'].value_counts().to_dict()}")
    print(f"  HER2 status: {harm['her2_status'].value_counts().to_dict()}")
    miss = {c: harm[c].isna().sum() for c in ['er_status', 'pr_status', 'her2_status', 'pam50_label'] if c in harm.columns}
    print(f"  Missing: {miss}")

    return harm


def fetch_tcga_pam50():
    """Fetch PAM50 subtype from cBioPortal for TCGA-BRCA."""
    cache_file = os.path.join(RAW_DIR, "tcga_pam50.csv")
    if os.path.exists(cache_file):
        return pd.read_csv(cache_file)

    # Try TCGA PanCancer Atlas study which has molecular subtypes
    print("  Fetching TCGA PAM50 from cBioPortal (PanCancer Atlas)...")
    base_url = "https://www.cbioportal.org/api"

    # Try brca_tcga_pan_can_atlas_2018 which has SUBTYPE
    url = f"{base_url}/studies/brca_tcga_pan_can_atlas_2018/clinical-data?clinicalDataType=SAMPLE&projection=DETAILED"
    try:
        r = requests.get(url, headers={"Accept": "application/json"}, timeout=120)
        if r.status_code == 200:
            data = r.json()
            sdf = pd.DataFrame(data)
            if 'clinicalAttributeId' in sdf.columns:
                sdf_pivot = sdf.pivot_table(
                    index=['patientId', 'sampleId'], columns='clinicalAttributeId',
                    values='value', aggfunc='first'
                ).reset_index()

                # Look for subtype column
                for col in sdf_pivot.columns:
                    if 'SUBTYPE' in col.upper():
                        print(f"    Found: {col} -> {sdf_pivot[col].value_counts().to_dict()}")

                if 'SUBTYPE' in sdf_pivot.columns:
                    pam50_map = sdf_pivot[['patientId', 'SUBTYPE']].copy()
                    pam50_map.columns = ['patient_id', 'pam50_label']
                    # Clean PAM50 labels
                    subtype_mapping = {
                        'BRCA_Basal': 'Basal',
                        'BRCA_Her2': 'Her2',
                        'BRCA_LumA': 'LumA',
                        'BRCA_LumB': 'LumB',
                        'BRCA_Normal': 'Normal',
                    }
                    pam50_map['pam50_label'] = pam50_map['pam50_label'].map(subtype_mapping)
                    pam50_map = pam50_map.dropna(subset=['pam50_label'])
                    pam50_map.to_csv(cache_file, index=False)
                    print(f"    PAM50 labels: {pam50_map['pam50_label'].value_counts().to_dict()}")
                    return pam50_map
    except Exception as e:
        print(f"    Error: {e}")

    return None


# ============================================================
# 4. Parse METABRIC
# ============================================================

def parse_metabric():
    print("\n=== Parsing METABRIC ===")
    df = pd.read_csv(os.path.join(RAW_DIR, "brca_metabric_clinical.tsv"), sep='\t')
    print(f"  Raw: {df.shape}")

    harm = pd.DataFrame()
    harm['sample_id'] = df['sampleId']
    harm['patient_id'] = df['patientId']
    harm['cohort'] = 'METABRIC'
    harm['platform'] = 'microarray'

    # PAM50 - CLAUDIN_SUBTYPE in METABRIC is the PAM50 subtype
    harm['pam50_label'] = df['CLAUDIN_SUBTYPE'].replace({'NC': np.nan})
    harm['pam50_source'] = 'published'

    # ER
    harm['er_status'] = df['ER_STATUS']
    if 'ER_IHC' in df.columns:
        harm['er_ihc'] = df['ER_IHC'].replace({'Positve': 'Positive'})  # Fix typo in data

    # PR
    harm['pr_status'] = df['PR_STATUS']

    # HER2
    harm['her2_status'] = df['HER2_STATUS']

    # Grade
    harm['grade'] = pd.to_numeric(df['GRADE'], errors='coerce')

    # Age
    harm['age'] = pd.to_numeric(df['AGE_AT_DIAGNOSIS'], errors='coerce')

    # Tumor size
    harm['tumor_size'] = pd.to_numeric(df['TUMOR_SIZE'], errors='coerce')

    # Stage
    harm['stage'] = df['TUMOR_STAGE']

    # Nodes
    harm['lymph_nodes_positive'] = pd.to_numeric(df['LYMPH_NODES_EXAMINED_POSITIVE'], errors='coerce')

    # Histology
    harm['histology'] = df['CANCER_TYPE_DETAILED']

    # Menopause
    harm['menopausal_state'] = df['INFERRED_MENOPAUSAL_STATE']

    # Survival
    harm['os_months'] = pd.to_numeric(df['OS_MONTHS'], errors='coerce')
    harm['os_status'] = df['OS_STATUS']

    print(f"  Harmonized: {harm.shape}")
    print(f"  PAM50: {harm['pam50_label'].value_counts().to_dict()}")
    print(f"  ER: {harm['er_status'].value_counts().to_dict()}")
    print(f"  Grade: {harm['grade'].value_counts().to_dict()}")

    return harm


# ============================================================
# 5. Combine all cohorts
# ============================================================

def combine_cohorts(dfs):
    print("\n=== Combining all cohorts ===")
    combined = pd.concat(dfs, ignore_index=True, sort=False)
    print(f"  Total: {combined.shape}")
    print(f"  By cohort: {combined['cohort'].value_counts().to_dict()}")

    # Standardize PAM50 labels
    pam50_std = {
        'Basal': 'Basal', 'basal': 'Basal', 'Basal-like': 'Basal',
        'Her2': 'Her2', 'her2': 'Her2', 'HER2-enriched': 'Her2', 'HER2': 'Her2',
        'LumA': 'LumA', 'lumA': 'LumA', 'Luminal A': 'LumA', 'luminal a': 'LumA',
        'LumB': 'LumB', 'lumB': 'LumB', 'Luminal B': 'LumB', 'luminal b': 'LumB',
        'Normal': 'Normal', 'normal': 'Normal', 'Normal-like': 'Normal',
        'claudin-low': 'Claudin-low',
    }
    combined['pam50_label'] = combined['pam50_label'].map(pam50_std)

    # Standardize ER/PR/HER2 status
    for col in ['er_status', 'pr_status', 'her2_status']:
        if col in combined.columns:
            pos_vals = ['Positive', 'positive', 'Pos', 'pos', '+', '1']
            neg_vals = ['Negative', 'negative', 'Neg', 'neg', '-', '0']
            combined[col] = combined[col].apply(
                lambda x: 'Positive' if str(x) in pos_vals else ('Negative' if str(x) in neg_vals else np.nan)
            )

    print(f"\n  PAM50 after standardization: {combined['pam50_label'].value_counts().to_dict()}")
    print(f"  PAM50 missing: {combined['pam50_label'].isna().sum()}")

    return combined


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    dfs = []

    # 1. GSE81538
    gse81538 = parse_gse81538()
    dfs.append(gse81538)

    # 2. GSE96058
    gse96058 = download_and_parse_gse96058()
    if not gse96058.empty:
        dfs.append(gse96058)

    # 3. TCGA-BRCA
    tcga = parse_tcga()
    dfs.append(tcga)

    # 4. METABRIC
    metabric = parse_metabric()
    dfs.append(metabric)

    # Combine
    combined = combine_cohorts(dfs)

    # Save
    combined.to_csv(os.path.join(PROC_DIR, "cohort_harmonized.csv"), index=False)
    print(f"\nSaved harmonized data: {combined.shape}")

    # Summary table
    summary = combined.groupby('cohort').agg(
        n=('sample_id', 'count'),
        pam50_available=('pam50_label', lambda x: x.notna().sum()),
        er_available=('er_status', lambda x: x.notna().sum()),
        pr_available=('pr_status', lambda x: x.notna().sum()),
        her2_available=('her2_status', lambda x: x.notna().sum()),
        ki67_available=('ki67', lambda x: x.notna().sum()) if 'ki67' in combined.columns else ('sample_id', lambda x: 0),
        grade_available=('grade', lambda x: x.notna().sum()) if 'grade' in combined.columns else ('sample_id', lambda x: 0),
    )
    print("\n=== Cohort Summary ===")
    print(summary.to_string())
    summary.to_csv(os.path.join(PROC_DIR, "cohort_summary.csv"))
