"""
Phase 1-2: Data Discovery, Acquisition and Initial Processing
Downloads and processes data from:
- GSE81538 (GEO) - Training/Discovery
- GSE96058 (GEO) - Training/Validation
- TCGA-BRCA (cBioPortal) - External Validation 1
- METABRIC (cBioPortal) - External Validation 2
"""

import os
import sys
import gzip
import io
import requests
import pandas as pd
import numpy as np
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")

os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROC_DIR, exist_ok=True)

LOG = []

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")
    LOG.append(f"[{ts}] {msg}")


# ============================================================
# 1. GEO: GSE81538 + GSE96058 metadata
# ============================================================

def download_geo_series_matrix(gse_id):
    """Download series matrix file from GEO."""
    out_path = os.path.join(RAW_DIR, f"{gse_id}_series_matrix.txt")
    if os.path.exists(out_path):
        log(f"{gse_id} series matrix already exists, skipping download")
        return out_path

    # Try different URL patterns
    urls = [
        f"https://ftp.ncbi.nlm.nih.gov/geo/series/{gse_id[:-3]}nnn/{gse_id}/matrix/{gse_id}_series_matrix.txt.gz",
    ]

    for url in urls:
        log(f"Downloading {gse_id} from {url}")
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200:
                content = gzip.decompress(r.content).decode('utf-8', errors='replace')
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                log(f"  -> Saved {len(content)} chars to {out_path}")
                return out_path
        except Exception as e:
            log(f"  -> Failed: {e}")

    log(f"WARNING: Could not download {gse_id}")
    return None


def parse_geo_series_matrix(filepath):
    """Parse GEO series matrix to extract sample metadata."""
    if filepath is None:
        return None

    metadata = {}
    data_start = None

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        line = line.strip()
        if line.startswith('!Sample_'):
            key = line.split('\t')[0].replace('!', '')
            values = line.split('\t')[1:]
            values = [v.strip('"') for v in values]
            metadata[key] = values
        if line.startswith('"ID_REF"') or line.startswith('!series_matrix_table_begin'):
            data_start = i

    if not metadata:
        return None

    # Build sample dataframe from metadata
    geo_accessions = metadata.get('Sample_geo_accession', [])
    df = pd.DataFrame({'sample_id': geo_accessions})

    # Extract characteristics
    char_keys = [k for k in metadata if 'characteristics' in k.lower() or 'Sample_characteristics_ch1' in k]

    # GEO stores characteristics as multiple rows with same key
    # We need to collect all characteristics
    char_rows = []
    for key in sorted(metadata.keys()):
        if 'characteristics_ch1' in key.lower():
            char_rows.append(metadata[key])

    for row_vals in char_rows:
        if len(row_vals) == len(geo_accessions):
            # Determine the key from the first value
            first_val = row_vals[0] if row_vals else ""
            if ':' in first_val:
                ckey = first_val.split(':')[0].strip()
                parsed = [v.split(':', 1)[1].strip() if ':' in v else v for v in row_vals]
                df[ckey] = parsed

    # Also extract title
    if 'Sample_title' in metadata and len(metadata['Sample_title']) == len(geo_accessions):
        df['title'] = metadata['Sample_title']

    return df


def download_geo_supp_file(gse_id, filename):
    """Download a supplementary file from GEO."""
    out_path = os.path.join(RAW_DIR, f"{gse_id}_{filename}")
    if os.path.exists(out_path):
        log(f"{gse_id} supp file {filename} already exists")
        return out_path

    url = f"https://ftp.ncbi.nlm.nih.gov/geo/series/{gse_id[:-3]}nnn/{gse_id}/suppl/{filename}"
    log(f"Downloading {url}")
    try:
        r = requests.get(url, timeout=300)
        if r.status_code == 200:
            with open(out_path, 'wb') as f:
                f.write(r.content)
            log(f"  -> Saved {len(r.content)} bytes")
            return out_path
    except Exception as e:
        log(f"  -> Failed: {e}")
    return None


# ============================================================
# 2. cBioPortal: TCGA-BRCA and METABRIC
# ============================================================

def download_cbioportal_clinical(study_id):
    """Download clinical data from cBioPortal API."""
    out_path = os.path.join(RAW_DIR, f"{study_id}_clinical.tsv")
    if os.path.exists(out_path):
        log(f"{study_id} clinical data already exists")
        return out_path

    base_url = "https://www.cbioportal.org/api"

    # Get clinical patient data
    log(f"Downloading {study_id} clinical patient data from cBioPortal...")
    url_patients = f"{base_url}/studies/{study_id}/clinical-data?clinicalDataType=PATIENT&projection=DETAILED"
    try:
        r = requests.get(url_patients, headers={"Accept": "application/json"}, timeout=120)
        if r.status_code == 200:
            patient_data = r.json()
            log(f"  -> Got {len(patient_data)} patient clinical entries")
        else:
            log(f"  -> Patient data failed: {r.status_code}")
            patient_data = []
    except Exception as e:
        log(f"  -> Patient data error: {e}")
        patient_data = []

    # Get clinical sample data
    log(f"Downloading {study_id} clinical sample data from cBioPortal...")
    url_samples = f"{base_url}/studies/{study_id}/clinical-data?clinicalDataType=SAMPLE&projection=DETAILED"
    try:
        r = requests.get(url_samples, headers={"Accept": "application/json"}, timeout=120)
        if r.status_code == 200:
            sample_data = r.json()
            log(f"  -> Got {len(sample_data)} sample clinical entries")
        else:
            log(f"  -> Sample data failed: {r.status_code}")
            sample_data = []
    except Exception as e:
        log(f"  -> Sample data error: {e}")
        sample_data = []

    # Pivot patient data
    if patient_data:
        pdf = pd.DataFrame(patient_data)
        if 'clinicalAttributeId' in pdf.columns and 'value' in pdf.columns:
            pdf_pivot = pdf.pivot_table(
                index='patientId', columns='clinicalAttributeId',
                values='value', aggfunc='first'
            ).reset_index()
        else:
            pdf_pivot = pdf
    else:
        pdf_pivot = pd.DataFrame()

    # Pivot sample data
    if sample_data:
        sdf = pd.DataFrame(sample_data)
        if 'clinicalAttributeId' in sdf.columns and 'value' in sdf.columns:
            sdf_pivot = sdf.pivot_table(
                index=['patientId', 'sampleId'], columns='clinicalAttributeId',
                values='value', aggfunc='first'
            ).reset_index()
        else:
            sdf_pivot = sdf
    else:
        sdf_pivot = pd.DataFrame()

    # Merge
    if not pdf_pivot.empty and not sdf_pivot.empty:
        merged = sdf_pivot.merge(pdf_pivot, on='patientId', how='left', suffixes=('', '_patient'))
    elif not sdf_pivot.empty:
        merged = sdf_pivot
    elif not pdf_pivot.empty:
        merged = pdf_pivot
    else:
        log(f"WARNING: No clinical data for {study_id}")
        return None

    merged.to_csv(out_path, sep='\t', index=False)
    log(f"  -> Saved merged clinical data: {merged.shape}")
    return out_path


def download_cbioportal_subtypes(study_id):
    """Try to get molecular subtype data from cBioPortal."""
    out_path = os.path.join(RAW_DIR, f"{study_id}_subtypes.tsv")
    if os.path.exists(out_path):
        log(f"{study_id} subtype data already exists")
        return out_path

    # For TCGA, the subtype info is often in clinical data already
    # For METABRIC, PAM50 is in the clinical annotations
    # We also try the molecular profiles endpoint
    base_url = "https://www.cbioportal.org/api"

    url = f"{base_url}/studies/{study_id}/molecular-profiles"
    try:
        r = requests.get(url, headers={"Accept": "application/json"}, timeout=60)
        if r.status_code == 200:
            profiles = r.json()
            profile_ids = [p['molecularProfileId'] for p in profiles]
            log(f"  -> {study_id} molecular profiles: {profile_ids}")
    except:
        pass

    return None


# ============================================================
# 3. Download supplementary/processed data files
# ============================================================

def download_cbioportal_tar(study_id):
    """Download the full study data from cBioPortal datahub."""
    out_dir = os.path.join(RAW_DIR, study_id)
    marker_file = os.path.join(out_dir, "_downloaded")
    if os.path.exists(marker_file):
        log(f"{study_id} datahub already downloaded")
        return out_dir

    os.makedirs(out_dir, exist_ok=True)

    # Download individual files from datahub
    datahub_base = f"https://raw.githubusercontent.com/cBioPortal/datahub/master/public/{study_id}"

    files_to_get = [
        "data_clinical_patient.txt",
        "data_clinical_sample.txt",
    ]

    for fname in files_to_get:
        url = f"{datahub_base}/{fname}"
        fpath = os.path.join(out_dir, fname)
        if os.path.exists(fpath):
            continue
        log(f"  Downloading {study_id}/{fname}...")
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                with open(fpath, 'w', encoding='utf-8') as f:
                    f.write(r.text)
                log(f"    -> OK ({len(r.text)} chars)")
            else:
                log(f"    -> Not found ({r.status_code})")
        except Exception as e:
            log(f"    -> Error: {e}")

    with open(marker_file, 'w') as f:
        f.write(datetime.now().isoformat())

    return out_dir


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    log("=" * 60)
    log("PHASE 1-2: DATA ACQUISITION")
    log("=" * 60)

    # --- GEO datasets ---
    log("\n--- GSE81538 ---")
    gse81538_matrix = download_geo_series_matrix("GSE81538")
    gse81538_meta = parse_geo_series_matrix(gse81538_matrix)
    if gse81538_meta is not None:
        gse81538_meta.to_csv(os.path.join(PROC_DIR, "GSE81538_metadata.csv"), index=False)
        log(f"GSE81538 metadata: {gse81538_meta.shape}, columns: {list(gse81538_meta.columns)}")

    log("\n--- GSE96058 ---")
    gse96058_matrix = download_geo_series_matrix("GSE96058")
    gse96058_meta = parse_geo_series_matrix(gse96058_matrix)
    if gse96058_meta is not None:
        gse96058_meta.to_csv(os.path.join(PROC_DIR, "GSE96058_metadata.csv"), index=False)
        log(f"GSE96058 metadata: {gse96058_meta.shape}, columns: {list(gse96058_meta.columns)}")

    # --- cBioPortal datasets ---
    log("\n--- TCGA-BRCA (cBioPortal) ---")
    tcga_clinical = download_cbioportal_clinical("brca_tcga")
    download_cbioportal_subtypes("brca_tcga")
    download_cbioportal_tar("brca_tcga")

    log("\n--- METABRIC (cBioPortal) ---")
    metabric_clinical = download_cbioportal_clinical("brca_metabric")
    download_cbioportal_subtypes("brca_metabric")
    download_cbioportal_tar("brca_metabric")

    # Save log
    with open(os.path.join(BASE_DIR, "data", "download_log.txt"), 'w') as f:
        f.write('\n'.join(LOG))

    log("\nDone! Check data/raw/ and data/processed/ for outputs.")
