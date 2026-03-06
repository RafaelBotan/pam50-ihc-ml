"""
Complete analysis pipeline:
- Phase 3: Harmonization (corrected)
- Phase 4: Target label definition
- Phase 5: IHQ surrogate baseline
- Phase 6: Split and leakage prevention
- Phase 7: Modeling
- Phase 8: Evaluation
- Phase 9: Sensitivity analyses
- Phase 10: Interpretation
- Figures and Tables generation
"""

import os
import sys
import warnings
import json

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from scipy import stats

from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import (
    confusion_matrix, classification_report, balanced_accuracy_score,
    f1_score, cohen_kappa_score, accuracy_score
)
import xgboost as xgb

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
FIG_DIR = os.path.join(BASE_DIR, "figures")
TAB_DIR = os.path.join(BASE_DIR, "tables")

os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(TAB_DIR, exist_ok=True)

plt.rcParams.update({
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'font.size': 10,
    'font.family': 'sans-serif',
    'axes.titlesize': 12,
    'axes.labelsize': 11,
    'figure.figsize': (10, 8),
})

PAM50_COLORS = {
    'Basal': '#CC79A7',
    'Her2': '#D55E00',
    'LumA': '#0072B2',
    'LumB': '#56B4E9',
}
# LabelEncoder sorts alphabetically: Basal=0, Her2=1, LumA=2, LumB=3
PAM50_ORDER = ['Basal', 'Her2', 'LumA', 'LumB']


# ============================================================
# PHASE 3: CORRECTED HARMONIZATION
# ============================================================

def build_harmonized_dataset():
    print("=" * 60)
    print("PHASE 3: BUILDING HARMONIZED DATASET")
    print("=" * 60)

    all_dfs = []

    # --- GSE81538 ---
    print("\n--- GSE81538 ---")
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
                if vals and ':' in vals[0]:
                    key_part = vals[0].split(':')[0].strip()
                    parsed = [v.split(':', 1)[1].strip() if ':' in v else v for v in vals]
                    if key_part not in metadata:
                        metadata[key_part] = parsed
                    else:
                        i = 2
                        while f"{key_part}_{i}" in metadata:
                            i += 1
                        metadata[f"{key_part}_{i}"] = parsed

    raw = pd.DataFrame(metadata)
    for col in raw.columns:
        if col not in ['sample_id', 'tissue', 'pam50 subtype']:
            raw[col] = pd.to_numeric(raw[col], errors='coerce')

    h1 = pd.DataFrame({
        'sample_id': raw['sample_id'],
        'cohort': 'GSE81538',
        'platform': 'RNA-seq',
        'pam50_label': raw['pam50 subtype'],
        'pam50_source': 'published',
        'er_status': (raw['er consensus'] > 0).map({True: 'Positive', False: 'Negative'}),
        'er_score': raw['er consensus'],
        'pr_status': (raw['pgr consensus'] > 0).map({True: 'Positive', False: 'Negative'}),
        'pr_score': raw['pgr consensus'],
        'her2_ihc_score': raw['her2 ihc clinreading'],
        'her2_status': raw.get('her2 clinical status', raw.get('her2 consensus', pd.Series())).map({0: 'Negative', 1: 'Positive'}),
        'ki67': raw['ki67 consensus'],
        'grade': raw['nhg consensus'],
    })
    print(f"  GSE81538: {h1.shape[0]} samples")
    all_dfs.append(h1)

    # --- GSE96058 ---
    print("\n--- GSE96058 ---")
    matrix_file = os.path.join(RAW_DIR, "GSE96058-GPL11154_series_matrix.txt")
    if os.path.exists(matrix_file):
        metadata2 = {}
        with open(matrix_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('!Sample_geo_accession'):
                    vals = line.split('\t')[1:]
                    metadata2['sample_id'] = [v.strip('"') for v in vals]
                elif line.startswith('!Sample_characteristics_ch1'):
                    vals = line.split('\t')[1:]
                    vals = [v.strip('"') for v in vals]
                    if vals and ':' in vals[0]:
                        key_part = vals[0].split(':')[0].strip()
                        parsed = [v.split(':', 1)[1].strip() if ':' in v else v for v in vals]
                        if key_part not in metadata2:
                            metadata2[key_part] = parsed
                        else:
                            i = 2
                            while f"{key_part}_{i}" in metadata2:
                                i += 1
                            metadata2[f"{key_part}_{i}"] = parsed

        raw2 = pd.DataFrame(metadata2)

        def map_status_01(series):
            return series.map(lambda x: 'Positive' if str(x).strip() in ['1', 'Positive']
                            else ('Negative' if str(x).strip() in ['0', 'Negative']
                            else np.nan))

        h2 = pd.DataFrame({
            'sample_id': raw2['sample_id'],
            'cohort': 'GSE96058',
            'platform': 'RNA-seq',
            'pam50_label': raw2.get('pam50 subtype', pd.Series(dtype=str)),
            'pam50_source': 'published',
        })

        if 'er status' in raw2.columns:
            h2['er_status'] = map_status_01(raw2['er status'])
        if 'pgr status' in raw2.columns:
            h2['pr_status'] = map_status_01(raw2['pgr status'])
        if 'her2 status' in raw2.columns:
            h2['her2_status'] = map_status_01(raw2['her2 status'])
        if 'ki67 status' in raw2.columns:
            # Ki67 in GSE96058 is binary (0/1) — map to high/low
            ki67_raw = raw2['ki67 status'].map(lambda x: str(x).strip())
            h2['ki67_high'] = ki67_raw.map({'1': True, '0': False, 'NA': np.nan, 'nan': np.nan, '': np.nan})
        if 'nhg' in raw2.columns:
            h2['grade'] = raw2['nhg'].map({'G1': 1.0, 'G2': 2.0, 'G3': 3.0})
        if 'age at diagnosis' in raw2.columns:
            h2['age'] = pd.to_numeric(raw2['age at diagnosis'], errors='coerce')
        if 'tumor size' in raw2.columns:
            h2['tumor_size'] = pd.to_numeric(raw2['tumor size'], errors='coerce')

        print(f"  GSE96058: {h2.shape[0]} samples, grade avail: {h2['grade'].notna().sum() if 'grade' in h2.columns else 0}")
        all_dfs.append(h2)

    # --- TCGA-BRCA ---
    print("\n--- TCGA-BRCA ---")
    tcga = pd.read_csv(os.path.join(RAW_DIR, "brca_tcga_clinical.tsv"), sep='\t')
    pam50_file = os.path.join(RAW_DIR, "tcga_pam50.csv")
    pam50_map = pd.read_csv(pam50_file) if os.path.exists(pam50_file) else None

    h3 = pd.DataFrame({
        'sample_id': tcga['sampleId'],
        'patient_id': tcga['patientId'],
        'cohort': 'TCGA-BRCA',
        'platform': 'RNA-seq',
        'pam50_source': 'TCGA_publication',
    })

    if pam50_map is not None:
        pam50_std = {
            'Luminal A': 'LumA', 'Luminal B': 'LumB',
            'Basal-like': 'Basal', 'HER2-enriched': 'Her2',
            'Normal-like': 'Normal'
        }
        pam50_map['pam50_label'] = pam50_map['pam50_label'].map(pam50_std)
        pam50_dict = dict(zip(pam50_map['patient_id'], pam50_map['pam50_label']))
        h3['pam50_label'] = h3['patient_id'].map(pam50_dict)
        print(f"  PAM50 mapped: {h3['pam50_label'].value_counts().to_dict()}")

    h3['er_status'] = tcga['ER_STATUS_BY_IHC'].replace(
        {'[Not Evaluated]': np.nan, 'Indeterminate': np.nan, '[Not Available]': np.nan})
    h3['pr_status'] = tcga['PR_STATUS_BY_IHC'].replace(
        {'[Not Evaluated]': np.nan, 'Indeterminate': np.nan, '[Not Available]': np.nan})

    her2_ihc = tcga['IHC_HER2'].replace(
        {'[Not Evaluated]': np.nan, 'Indeterminate': np.nan, '[Not Available]': np.nan})
    her2_fish = tcga.get('HER2_FISH_STATUS', pd.Series(dtype=str)).replace(
        {'[Not Evaluated]': np.nan, 'Indeterminate': np.nan, '[Not Available]': np.nan, 'Equivocal': np.nan})
    h3['her2_status'] = her2_ihc.replace({'Equivocal': np.nan})
    mask_eq = her2_ihc == 'Equivocal'
    h3.loc[mask_eq & (her2_fish == 'Positive'), 'her2_status'] = 'Positive'
    h3.loc[mask_eq & (her2_fish == 'Negative'), 'her2_status'] = 'Negative'

    if 'AGE' in tcga.columns:
        h3['age'] = pd.to_numeric(tcga['AGE'], errors='coerce')

    print(f"  TCGA: {h3.shape[0]} samples, PAM50 available: {h3['pam50_label'].notna().sum() if 'pam50_label' in h3.columns else 0}")
    all_dfs.append(h3)

    # --- METABRIC ---
    print("\n--- METABRIC ---")
    mb = pd.read_csv(os.path.join(RAW_DIR, "brca_metabric_clinical.tsv"), sep='\t')

    h4 = pd.DataFrame({
        'sample_id': mb['sampleId'],
        'patient_id': mb['patientId'],
        'cohort': 'METABRIC',
        'platform': 'microarray',
        'pam50_label': mb['CLAUDIN_SUBTYPE'].replace({'NC': np.nan}),
        'pam50_source': 'published',
        'er_status': mb['ER_STATUS'],
        'pr_status': mb['PR_STATUS'],
        'her2_status': mb['HER2_STATUS'],
        'grade': pd.to_numeric(mb['GRADE'], errors='coerce'),
        'age': pd.to_numeric(mb['AGE_AT_DIAGNOSIS'], errors='coerce'),
        'tumor_size': pd.to_numeric(mb['TUMOR_SIZE'], errors='coerce'),
        'histology': mb['CANCER_TYPE_DETAILED'],
        'os_months': pd.to_numeric(mb['OS_MONTHS'], errors='coerce'),
        'os_status': mb['OS_STATUS'],
    })
    if 'LYMPH_NODES_EXAMINED_POSITIVE' in mb.columns:
        h4['lymph_nodes_positive'] = pd.to_numeric(mb['LYMPH_NODES_EXAMINED_POSITIVE'], errors='coerce')

    print(f"  METABRIC: {h4.shape[0]} samples")
    all_dfs.append(h4)

    # --- Combine ---
    combined = pd.concat(all_dfs, ignore_index=True, sort=False)

    # Standardize PAM50 labels
    pam50_std_map = {
        'Basal': 'Basal', 'basal': 'Basal', 'Basal-like': 'Basal',
        'Her2': 'Her2', 'her2': 'Her2', 'HER2-enriched': 'Her2', 'HER2': 'Her2',
        'LumA': 'LumA', 'lumA': 'LumA', 'Luminal A': 'LumA',
        'LumB': 'LumB', 'lumB': 'LumB', 'Luminal B': 'LumB',
        'Normal': 'Normal', 'normal': 'Normal', 'Normal-like': 'Normal',
        'claudin-low': 'Claudin-low',
    }
    combined['pam50_label'] = combined['pam50_label'].map(pam50_std_map)

    for col in ['er_status', 'pr_status', 'her2_status']:
        combined[col] = combined[col].apply(
            lambda x: 'Positive' if str(x).strip() in ['Positive', 'positive', '1', '+']
            else ('Negative' if str(x).strip() in ['Negative', 'negative', '0', '-']
            else np.nan)
        )

    print(f"\n  Combined total: {combined.shape[0]}")
    print(f"  PAM50: {combined['pam50_label'].value_counts().to_dict()}")

    combined.to_csv(os.path.join(PROC_DIR, "harmonized_full.csv"), index=False)
    return combined


# ============================================================
# PHASE 4: TARGET LABEL DEFINITION
# ============================================================

def define_target(df):
    print("\n" + "=" * 60)
    print("PHASE 4: TARGET LABEL DEFINITION (4 classes)")
    print("=" * 60)

    df_target = df[df['pam50_label'].isin(PAM50_ORDER)].copy()
    print(f"  Excluded Normal-like: {(df['pam50_label']=='Normal').sum()}")
    print(f"  Excluded Claudin-low: {(df['pam50_label']=='Claudin-low').sum()}")
    print(f"  Excluded missing PAM50: {df['pam50_label'].isna().sum()}")
    print(f"  Remaining (4-class): {len(df_target)}")
    print(f"  By class: {df_target['pam50_label'].value_counts().to_dict()}")
    print(f"  By cohort: {df_target.groupby('cohort')['pam50_label'].count().to_dict()}")
    return df_target


# ============================================================
# PHASE 5: IHQ SURROGATE BASELINE
# ============================================================

def create_ihq_surrogate(df):
    print("\n" + "=" * 60)
    print("PHASE 5: IHQ SURROGATE BASELINE")
    print("=" * 60)

    df = df.copy()
    df['hr_positive'] = (df['er_status'] == 'Positive') | (df['pr_status'] == 'Positive')
    df['hr_negative'] = (df['er_status'] == 'Negative') & (df['pr_status'] == 'Negative')

    # Ki67 high/low: use continuous ki67 if available, otherwise ki67_high, otherwise grade
    df['_ki67_high'] = np.nan
    if 'ki67' in df.columns:
        mask_ki67 = df['ki67'].notna()
        df.loc[mask_ki67, '_ki67_high'] = (df.loc[mask_ki67, 'ki67'] >= 20)
    if 'ki67_high' in df.columns:
        mask_fill = df['_ki67_high'].isna() & df['ki67_high'].notna()
        df.loc[mask_fill, '_ki67_high'] = df.loc[mask_fill, 'ki67_high']
    if 'grade' in df.columns:
        mask_fill = df['_ki67_high'].isna() & df['grade'].notna()
        df.loc[mask_fill & (df['grade'] == 3), '_ki67_high'] = True
        df.loc[mask_fill & (df['grade'].isin([1, 2])), '_ki67_high'] = False

    # Classification
    tn = df['hr_negative'] & (df['her2_status'] == 'Negative')
    her2_pos = df['hr_negative'] & (df['her2_status'] == 'Positive')
    lumB_her2 = df['hr_positive'] & (df['her2_status'] == 'Positive')
    lumB_her2neg = df['hr_positive'] & (df['her2_status'] == 'Negative') & (df['_ki67_high'] == True)
    lumA = df['hr_positive'] & (df['her2_status'] == 'Negative') & (df['_ki67_high'] == False)

    df['ihq_surrogate'] = np.nan
    df.loc[tn, 'ihq_surrogate'] = 'Triple-negative'
    df.loc[her2_pos, 'ihq_surrogate'] = 'HER2-positive'
    df.loc[lumB_her2, 'ihq_surrogate'] = 'Luminal B-like'
    df.loc[lumB_her2neg, 'ihq_surrogate'] = 'Luminal B-like'
    df.loc[lumA, 'ihq_surrogate'] = 'Luminal A-like'

    surrogate_to_pam50 = {
        'Luminal A-like': 'LumA',
        'Luminal B-like': 'LumB',
        'HER2-positive': 'Her2',
        'Triple-negative': 'Basal',
    }
    df['ihq_as_pam50'] = df['ihq_surrogate'].map(surrogate_to_pam50)

    classified = df['ihq_surrogate'].notna().sum()
    print(f"  Classified: {classified}/{len(df)} ({100*classified/len(df):.1f}%)")
    print(f"  Surrogate: {df['ihq_surrogate'].value_counts().to_dict()}")
    return df


# ============================================================
# PHASE 6: FEATURE ENGINEERING
# ============================================================

def prepare_features(df):
    print("\n" + "=" * 60)
    print("PHASE 6: FEATURE ENGINEERING")
    print("=" * 60)

    df = df.copy()
    df['er_binary'] = (df['er_status'] == 'Positive').astype(float)
    df['pr_binary'] = (df['pr_status'] == 'Positive').astype(float)
    df['her2_binary'] = (df['her2_status'] == 'Positive').astype(float)
    df.loc[df['er_status'].isna(), 'er_binary'] = np.nan
    df.loc[df['pr_status'].isna(), 'pr_binary'] = np.nan
    df.loc[df['her2_status'].isna(), 'her2_binary'] = np.nan

    # For ki67: use continuous where available, else binary
    if 'ki67' not in df.columns:
        df['ki67'] = np.nan
    if 'ki67_high' in df.columns:
        mask = df['ki67'].isna() & df['ki67_high'].notna()
        df.loc[mask & (df['ki67_high'] == True), 'ki67'] = 30.0  # proxy
        df.loc[mask & (df['ki67_high'] == False), 'ki67'] = 10.0  # proxy

    # Feature sets — adapted to data availability
    # Set 1: ER, PR, HER2 (binary) — available in all cohorts
    # Set 2: ER, PR, HER2, Grade — available in GSE81538, GSE96058 (partial), METABRIC
    # Set 3: ER, PR, HER2, Ki67, Grade — available in GSE81538, GSE96058 (proxy), METABRIC (partial)
    feature_sets = {
        'Set 1 (Core IHQ)': ['er_binary', 'pr_binary', 'her2_binary'],
        'Set 2 (IHQ + Grade)': ['er_binary', 'pr_binary', 'her2_binary', 'grade'],
        'Set 3 (IHQ + Ki67 + Grade)': ['er_binary', 'pr_binary', 'her2_binary', 'ki67', 'grade'],
    }

    for set_name, feats in feature_sets.items():
        available = [f for f in feats if f in df.columns]
        for cohort in sorted(df['cohort'].unique()):
            mask = df['cohort'] == cohort
            n_total = mask.sum()
            n_complete = df.loc[mask, available].dropna().shape[0]
            print(f"  {set_name} | {cohort}: {n_complete}/{n_total} ({100*n_complete/n_total:.0f}%)")

    return df, feature_sets


# ============================================================
# PHASE 7-8: MODELING AND EVALUATION
# ============================================================

def train_and_evaluate(df, feature_sets):
    print("\n" + "=" * 60)
    print("PHASE 7-8: MODELING AND EVALUATION")
    print("=" * 60)

    results = {}
    all_predictions = {}

    train_cohorts = ['GSE81538', 'GSE96058']
    val_cohorts = {
        'TCGA-BRCA': 'External Validation 1',
        'METABRIC': 'External Validation 2',
    }

    le = LabelEncoder()
    le.fit(PAM50_ORDER)  # Alphabetical: Basal=0, Her2=1, LumA=2, LumB=3

    for set_name, features in feature_sets.items():
        print(f"\n--- {set_name} ---")
        available_features = [f for f in features if f in df.columns]

        # Training data
        train_mask = df['cohort'].isin(train_cohorts) & df['pam50_label'].isin(PAM50_ORDER)
        train_data = df.loc[train_mask].dropna(subset=available_features + ['pam50_label'])

        if len(train_data) < 50:
            print(f"  Too few training samples ({len(train_data)}), skipping")
            continue

        X_train = train_data[available_features].values.astype(float)
        y_train = le.transform(train_data['pam50_label'])

        class_dist = {le.classes_[i]: int(c) for i, c in enumerate(np.bincount(y_train, minlength=4))}
        print(f"  Training: {len(train_data)} samples")
        print(f"  Features: {available_features}")
        print(f"  Classes: {class_dist}")

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)

        models = {
            'Logistic Regression': LogisticRegression(
                solver='lbfgs', max_iter=2000, C=1.0, class_weight='balanced'
            ),
            'Random Forest': RandomForestClassifier(
                n_estimators=500, max_depth=None,
                class_weight='balanced', random_state=42, n_jobs=-1
            ),
            'XGBoost': xgb.XGBClassifier(
                n_estimators=500, max_depth=6, learning_rate=0.1,
                objective='multi:softprob', num_class=4,
                eval_metric='mlogloss', random_state=42,
                verbosity=0
            ),
        }

        # Internal 5-fold CV
        print("\n  Internal 5-fold CV:")
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
        for model_name, model in models.items():
            X_in = X_train_scaled if 'Logistic' in model_name else X_train
            y_pred_cv = cross_val_predict(model, X_in, y_train, cv=cv)
            f1_cv = f1_score(y_train, y_pred_cv, average='macro')
            kappa_cv = cohen_kappa_score(y_train, y_pred_cv)
            ba_cv = balanced_accuracy_score(y_train, y_pred_cv)
            print(f"    {model_name}: F1={f1_cv:.3f}, κ={kappa_cv:.3f}, BA={ba_cv:.3f}")

            # Store CV results
            key_cv = (set_name, model_name, 'Internal CV')
            results[key_cv] = {
                'feature_set': set_name, 'model': model_name,
                'validation_cohort': 'Internal CV', 'n': len(train_data),
                'accuracy': accuracy_score(y_train, y_pred_cv),
                'balanced_accuracy': ba_cv, 'macro_f1': f1_cv, 'kappa': kappa_cv,
            }
            all_predictions[key_cv] = {
                'y_true': y_train, 'y_pred': y_pred_cv, 'y_prob': None,
            }

        # Fit on full training set
        fitted_models = {}
        for model_name, model in models.items():
            X_in = X_train_scaled if 'Logistic' in model_name else X_train
            model.fit(X_in, y_train)
            fitted_models[model_name] = model

        # External validation
        for val_cohort, val_label in val_cohorts.items():
            print(f"\n  {val_label} ({val_cohort}):")
            val_mask = (df['cohort'] == val_cohort) & df['pam50_label'].isin(PAM50_ORDER)
            val_data = df.loc[val_mask].dropna(subset=available_features + ['pam50_label'])

            if len(val_data) < 20:
                print(f"    Too few samples ({len(val_data)}), skipping")
                continue

            X_val = val_data[available_features].values.astype(float)
            y_val = le.transform(val_data['pam50_label'])
            X_val_scaled = scaler.transform(X_val)

            val_class_dist = {le.classes_[i]: int(c) for i, c in enumerate(np.bincount(y_val, minlength=4))}
            print(f"    N={len(val_data)}, classes: {val_class_dist}")

            for model_name, model in fitted_models.items():
                X_in = X_val_scaled if 'Logistic' in model_name else X_val
                y_pred = model.predict(X_in)
                y_prob = model.predict_proba(X_in)

                f1 = f1_score(y_val, y_pred, average='macro')
                kappa = cohen_kappa_score(y_val, y_pred)
                ba = balanced_accuracy_score(y_val, y_pred)
                acc = accuracy_score(y_val, y_pred)

                key = (set_name, model_name, val_cohort)
                results[key] = {
                    'feature_set': set_name, 'model': model_name,
                    'validation_cohort': val_cohort, 'n': len(val_data),
                    'accuracy': acc, 'balanced_accuracy': ba,
                    'macro_f1': f1, 'kappa': kappa,
                }
                all_predictions[key] = {
                    'y_true': y_val, 'y_pred': y_pred, 'y_prob': y_prob,
                    'sample_ids': val_data['sample_id'].values,
                }
                print(f"    {model_name}: acc={acc:.3f}, BA={ba:.3f}, F1={f1:.3f}, κ={kappa:.3f}")

        # IHQ Surrogate baseline on validation + training
        for cohort_name in list(val_cohorts.keys()) + ['GSE81538', 'GSE96058']:
            label = val_cohorts.get(cohort_name, cohort_name)
            surr_mask = (df['cohort'] == cohort_name) & df['pam50_label'].isin(PAM50_ORDER) & df['ihq_as_pam50'].isin(PAM50_ORDER)
            surr_data = df.loc[surr_mask]

            if len(surr_data) < 20:
                continue

            y_true_s = le.transform(surr_data['pam50_label'])
            y_pred_s = le.transform(surr_data['ihq_as_pam50'])

            f1_s = f1_score(y_true_s, y_pred_s, average='macro')
            kappa_s = cohen_kappa_score(y_true_s, y_pred_s)
            ba_s = balanced_accuracy_score(y_true_s, y_pred_s)
            acc_s = accuracy_score(y_true_s, y_pred_s)

            key_s = (set_name, 'IHQ Surrogate', cohort_name)
            if key_s not in results:
                results[key_s] = {
                    'feature_set': set_name, 'model': 'IHQ Surrogate',
                    'validation_cohort': cohort_name, 'n': len(surr_data),
                    'accuracy': acc_s, 'balanced_accuracy': ba_s,
                    'macro_f1': f1_s, 'kappa': kappa_s,
                }
                all_predictions[key_s] = {
                    'y_true': y_true_s, 'y_pred': y_pred_s, 'y_prob': None,
                }
                print(f"\n  IHQ Surrogate ({cohort_name}): N={len(surr_data)}, acc={acc_s:.3f}, F1={f1_s:.3f}, κ={kappa_s:.3f}")

    return results, all_predictions, fitted_models, scaler, le


# ============================================================
# FIGURES
# ============================================================

def generate_figures(df, results, predictions, le):
    print("\n" + "=" * 60)
    print("GENERATING FIGURES")
    print("=" * 60)

    fig1_flowchart(df)
    fig2_cohort_characteristics(df)
    fig3_confusion_matrices(predictions, le)
    fig4_performance_comparison(results)
    fig5_feature_importance(df, le)
    fig6_discordance_analysis(df, le)


def fig1_flowchart(df):
    print("  Figure 1: Study design")
    fig, ax = plt.subplots(figsize=(14, 10))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    ax.text(5, 9.5, 'Study Design: PAM50-Like Classifier from Routine Pathology Data',
            ha='center', va='center', fontsize=14, fontweight='bold')

    boxes = [
        (1.5, 7.5, f'GSE81538\n(n=405)\nDiscovery', '#E8F5E9'),
        (4.5, 7.5, f'GSE96058\n(n=3,069)\nTraining', '#E8F5E9'),
        (7.5, 7.5, 'Combined Training\n(n≈3,474)', '#C8E6C9'),
        (2.5, 5.0, f'TCGA-BRCA\n(n=519 w/ PAM50)\nExt. Validation 1', '#E3F2FD'),
        (7.0, 5.0, f'METABRIC\n(n=1,608 4-class)\nExt. Validation 2', '#E3F2FD'),
    ]
    for x, y, text, color in boxes:
        bbox = dict(boxstyle='round,pad=0.5', facecolor=color, edgecolor='gray', linewidth=1.5)
        ax.text(x, y, text, ha='center', va='center', fontsize=10, bbox=bbox)

    for x1, y1, x2, y2 in [(1.5, 7.0, 6.5, 7.0), (4.5, 7.0, 6.5, 7.0),
                             (5.0, 6.8, 2.5, 5.7), (5.5, 6.8, 7.0, 5.7)]:
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', lw=1.5, color='gray'))

    analysis_text = (
        'Analysis Pipeline\n'
        '────────────────────\n'
        '1. IHQ Surrogate Baseline\n'
        '2. Logistic Regression\n'
        '3. Random Forest\n'
        '4. XGBoost\n'
        '────────────────────\n'
        'Feature Sets:\n'
        'Set 1: ER, PR, HER2\n'
        'Set 2: + Grade\n'
        'Set 3: + Ki67, Grade'
    )
    bbox = dict(boxstyle='round,pad=0.5', facecolor='#FFF3E0', edgecolor='orange', linewidth=1.5)
    ax.text(5, 2.5, analysis_text, ha='center', va='center', fontsize=9, bbox=bbox, family='monospace')

    ax.text(5, 0.5, 'Primary Endpoint: Macro-F1 for 4-class PAM50 prediction\n'
            'Secondary: Cohen\'s κ, Balanced Accuracy, Per-class Sensitivity',
            ha='center', va='center', fontsize=10, style='italic',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='#FCE4EC', edgecolor='gray'))

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig1_study_design.png'), bbox_inches='tight')
    plt.close()


def fig2_cohort_characteristics(df):
    print("  Figure 2: Cohort characteristics")
    df_4 = df[df['pam50_label'].isin(PAM50_ORDER)].copy()

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))

    # PAM50 distribution
    ax = axes[0, 0]
    ct = pd.crosstab(df_4['cohort'], df_4['pam50_label'], normalize='index')
    ct = ct.reindex(columns=PAM50_ORDER, fill_value=0)
    ct.plot(kind='bar', stacked=True, ax=ax, color=[PAM50_COLORS[s] for s in PAM50_ORDER])
    ax.set_title('PAM50 Subtype Distribution')
    ax.set_ylabel('Proportion')
    ax.set_xlabel('')
    ax.legend(title='PAM50', bbox_to_anchor=(1.0, 1.0), fontsize=8)
    ax.tick_params(axis='x', rotation=45)

    # ER status
    ax = axes[0, 1]
    ct_er = pd.crosstab(df_4['cohort'], df_4['er_status'], normalize='index')
    ct_er.plot(kind='bar', stacked=True, ax=ax, color=['#e74c3c', '#2ecc71'])
    ax.set_title('ER Status')
    ax.set_ylabel('Proportion')
    ax.set_xlabel('')
    ax.tick_params(axis='x', rotation=45)

    # HER2 status
    ax = axes[0, 2]
    ct_h2 = pd.crosstab(df_4['cohort'], df_4['her2_status'], normalize='index')
    ct_h2.plot(kind='bar', stacked=True, ax=ax, color=['#e74c3c', '#2ecc71'])
    ax.set_title('HER2 Status')
    ax.set_ylabel('Proportion')
    ax.set_xlabel('')
    ax.tick_params(axis='x', rotation=45)

    # Grade
    ax = axes[1, 0]
    df_grade = df_4.dropna(subset=['grade'])
    if len(df_grade) > 0:
        ct_gr = pd.crosstab(df_grade['cohort'], df_grade['grade'], normalize='index')
        ct_gr.plot(kind='bar', stacked=True, ax=ax, color=['#3498db', '#f39c12', '#e74c3c'])
        ax.set_title('Histologic Grade')
        ax.set_ylabel('Proportion')
        ax.set_xlabel('')
        ax.tick_params(axis='x', rotation=45)

    # Ki67 (GSE81538)
    ax = axes[1, 1]
    if 'ki67' in df_4.columns:
        df_ki67 = df_4[df_4['cohort'] == 'GSE81538'].dropna(subset=['ki67'])
        if len(df_ki67) > 0:
            for subtype in PAM50_ORDER:
                subset = df_ki67[df_ki67['pam50_label'] == subtype]['ki67']
                if len(subset) > 0:
                    ax.hist(subset, bins=20, alpha=0.6, label=subtype, color=PAM50_COLORS[subtype])
            ax.set_title('Ki67 by PAM50 (GSE81538)')
            ax.set_xlabel('Ki67 (%)')
            ax.set_ylabel('Count')
            ax.legend(fontsize=8)
            ax.axvline(x=20, color='red', linestyle='--', alpha=0.5, label='20% cutoff')

    # Sample sizes
    ax = axes[1, 2]
    cohort_n = df_4.groupby('cohort').size().reindex(['GSE81538', 'GSE96058', 'TCGA-BRCA', 'METABRIC'])
    colors = ['#4CAF50', '#4CAF50', '#2196F3', '#2196F3']
    bars = ax.bar(range(len(cohort_n)), cohort_n.values, color=colors)
    ax.set_xticks(range(len(cohort_n)))
    ax.set_xticklabels(cohort_n.index, rotation=45)
    ax.set_title('Sample Size (4-class PAM50)')
    ax.set_ylabel('N')
    for i, v in enumerate(cohort_n.values):
        ax.text(i, v + 20, str(v), ha='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig2_cohort_characteristics.png'), bbox_inches='tight')
    plt.close()


def fig3_confusion_matrices(predictions, le):
    print("  Figure 3: Confusion matrices")

    # Select the best feature set for each cohort + IHQ surrogate
    keys_to_plot = []
    # Prioritize: Set 2 or Set 1, for external validation cohorts
    for cohort in ['TCGA-BRCA', 'METABRIC']:
        for set_pref in ['Set 2', 'Set 1']:
            for key in predictions:
                sn, mn, co = key
                if co == cohort and set_pref in sn:
                    keys_to_plot.append(key)
            if any(k[2] == cohort for k in keys_to_plot):
                break

    if not keys_to_plot:
        keys_to_plot = list(predictions.keys())[:8]

    n_plots = min(len(keys_to_plot), 8)
    ncols = min(4, n_plots)
    nrows = max(1, (n_plots + ncols - 1) // ncols)

    fig, axes = plt.subplots(nrows, ncols, figsize=(5 * ncols, 5 * nrows))
    axes = np.atleast_2d(axes)
    if axes.shape[0] == 1 and nrows > 1:
        axes = axes.T

    for idx, key in enumerate(keys_to_plot[:n_plots]):
        row, col = divmod(idx, ncols)
        ax = axes[row, col] if nrows > 1 else axes[0, col]

        pred = predictions[key]
        cm = confusion_matrix(pred['y_true'], pred['y_pred'], labels=range(4))
        cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)

        sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues',
                    xticklabels=PAM50_ORDER, yticklabels=PAM50_ORDER,
                    ax=ax, vmin=0, vmax=1, cbar=False)

        for i in range(4):
            for j in range(4):
                ax.text(j + 0.5, i + 0.75, f'(n={cm[i, j]})',
                       ha='center', va='center', fontsize=7, color='gray')

        sn, mn, co = key
        ax.set_title(f'{mn}\n{co}', fontsize=9)
        ax.set_ylabel('True PAM50')
        ax.set_xlabel('Predicted')

    for idx in range(n_plots, nrows * ncols):
        row, col = divmod(idx, ncols)
        (axes[row, col] if nrows > 1 else axes[0, col]).axis('off')

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig3_confusion_matrices.png'), bbox_inches='tight')
    plt.close()


def fig4_performance_comparison(results):
    print("  Figure 4: Performance comparison")

    if not results:
        return

    rdf = pd.DataFrame(results.values())

    # Bar chart: grouped by model, colored by cohort, for each metric
    fig, axes = plt.subplots(1, 3, figsize=(18, 7))
    metrics = ['macro_f1', 'kappa', 'balanced_accuracy']
    labels = ['Macro F1-Score', "Cohen's Kappa", 'Balanced Accuracy']

    # Filter to one feature set per model (best one per model+cohort)
    # Use the best F1 per model+cohort
    best_rows = []
    for (model, cohort), grp in rdf.groupby(['model', 'validation_cohort']):
        best_rows.append(grp.loc[grp['macro_f1'].idxmax()])
    best_df = pd.DataFrame(best_rows)

    for ax, metric, label in zip(axes, metrics, labels):
        pivot = best_df.pivot_table(index='model', columns='validation_cohort', values=metric, aggfunc='max')
        # Reorder
        model_order = ['IHQ Surrogate', 'Logistic Regression', 'Random Forest', 'XGBoost']
        pivot = pivot.reindex([m for m in model_order if m in pivot.index])
        pivot.plot(kind='bar', ax=ax, width=0.7)
        ax.set_title(label, fontsize=13)
        ax.set_ylim(0, 1)
        ax.set_xlabel('')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend(title='Cohort', fontsize=8)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig4_performance_comparison.png'), bbox_inches='tight')
    plt.close()


def fig5_feature_importance(df, le):
    print("  Figure 5: Feature importance")

    train_cohorts = ['GSE81538', 'GSE96058']
    features = ['er_binary', 'pr_binary', 'her2_binary', 'ki67', 'grade']
    available = [f for f in features if f in df.columns]

    train_mask = df['cohort'].isin(train_cohorts) & df['pam50_label'].isin(PAM50_ORDER)
    train_data = df.loc[train_mask].dropna(subset=available + ['pam50_label'])

    if len(train_data) < 50:
        print("    Too few samples")
        return

    X = train_data[available].values.astype(float)
    y = le.transform(train_data['pam50_label'])

    model = xgb.XGBClassifier(
        n_estimators=500, max_depth=6, learning_rate=0.1,
        objective='multi:softprob', num_class=4,
        eval_metric='mlogloss', random_state=42, verbosity=0
    )
    model.fit(X, y)

    importance = model.feature_importances_
    sorted_idx = np.argsort(importance)[::-1]

    fig, ax = plt.subplots(figsize=(8, 5))
    names = [available[i].replace('_binary', '').replace('_', ' ').upper() for i in sorted_idx]
    ax.barh(range(len(importance)), importance[sorted_idx], color='#2196F3')
    ax.set_yticks(range(len(importance)))
    ax.set_yticklabels(names)
    ax.set_xlabel('Feature Importance (Gain)')
    ax.set_title('XGBoost Feature Importance\n(Training: GSE81538 + GSE96058)')
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig5_feature_importance.png'), bbox_inches='tight')
    plt.close()


def fig6_discordance_analysis(df, le):
    print("  Figure 6: Discordance analysis")

    df_disc = df.dropna(subset=['pam50_label', 'ihq_as_pam50'])
    df_disc = df_disc[df_disc['pam50_label'].isin(PAM50_ORDER) & df_disc['ihq_as_pam50'].isin(PAM50_ORDER)]

    if len(df_disc) < 50:
        print("    Too few samples")
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Discordance rate by true PAM50
    ax = axes[0]
    disc_by_subtype = {}
    for subtype in PAM50_ORDER:
        mask = df_disc['pam50_label'] == subtype
        if mask.sum() > 0:
            disc_by_subtype[subtype] = (df_disc.loc[mask, 'ihq_as_pam50'] != subtype).mean()
    bars = ax.bar(disc_by_subtype.keys(), disc_by_subtype.values(),
                  color=[PAM50_COLORS[s] for s in disc_by_subtype.keys()])
    ax.set_ylabel('Discordance Rate')
    ax.set_title('IHQ Surrogate Discordance\nvs True PAM50 (All Cohorts)')
    ax.set_ylim(0, 1)
    for bar, (k, v) in zip(bars, disc_by_subtype.items()):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.02, f'{v:.1%}', ha='center', fontsize=10)

    # Confusion matrix: IHQ surrogate vs PAM50
    ax = axes[1]
    cm = confusion_matrix(le.transform(df_disc['pam50_label']),
                          le.transform(df_disc['ihq_as_pam50']), labels=range(4))
    cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='OrRd',
                xticklabels=PAM50_ORDER, yticklabels=PAM50_ORDER,
                ax=ax, vmin=0, vmax=1)
    ax.set_xlabel('IHQ Surrogate')
    ax.set_ylabel('True PAM50')
    ax.set_title('IHQ Surrogate vs PAM50\n(Normalized)')

    # Discordance by cohort
    ax = axes[2]
    disc_by_cohort = {}
    for cohort in df_disc['cohort'].unique():
        mask = df_disc['cohort'] == cohort
        disc_by_cohort[cohort] = (df_disc.loc[mask, 'ihq_as_pam50'] != df_disc.loc[mask, 'pam50_label']).mean()
    ax.bar(disc_by_cohort.keys(), disc_by_cohort.values(), color='#FF9800')
    ax.set_ylabel('Overall Discordance Rate')
    ax.set_title('IHQ Surrogate Discordance\nby Cohort')
    ax.set_ylim(0, 1)
    ax.tick_params(axis='x', rotation=45)
    for i, (k, v) in enumerate(disc_by_cohort.items()):
        ax.text(i, v + 0.02, f'{v:.1%}', ha='center', fontsize=10)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig6_discordance_analysis.png'), bbox_inches='tight')
    plt.close()


# ============================================================
# TABLES
# ============================================================

def generate_tables(df, results, predictions, le):
    print("\n" + "=" * 60)
    print("GENERATING TABLES")
    print("=" * 60)
    table1_cohort_characteristics(df)
    table2_performance(results)
    table3_perclass(predictions, le)
    table4_missing(df)


def table1_cohort_characteristics(df):
    print("  Table 1: Cohort characteristics")
    df_4 = df[df['pam50_label'].isin(PAM50_ORDER)]

    rows = []
    for cohort in ['GSE81538', 'GSE96058', 'TCGA-BRCA', 'METABRIC']:
        c = df_4[df_4['cohort'] == cohort]
        n = len(c)
        if n == 0:
            continue
        row = {
            'Cohort': cohort, 'N': n,
            'Role': 'Training' if cohort in ['GSE81538', 'GSE96058'] else 'External Validation',
            'Platform': c['platform'].iloc[0],
        }
        for s in PAM50_ORDER:
            ns = (c['pam50_label'] == s).sum()
            row[f'PAM50 {s}'] = f"{ns} ({100*ns/n:.1f}%)"

        er_pos = (c['er_status'] == 'Positive').sum()
        er_avail = c['er_status'].notna().sum()
        row['ER+ n (%)'] = f"{er_pos} ({100*er_pos/max(er_avail,1):.1f}%)" if er_avail > 0 else "N/A"

        pr_pos = (c['pr_status'] == 'Positive').sum()
        pr_avail = c['pr_status'].notna().sum()
        row['PR+ n (%)'] = f"{pr_pos} ({100*pr_pos/max(pr_avail,1):.1f}%)" if pr_avail > 0 else "N/A"

        h2_pos = (c['her2_status'] == 'Positive').sum()
        h2_avail = c['her2_status'].notna().sum()
        row['HER2+ n (%)'] = f"{h2_pos} ({100*h2_pos/max(h2_avail,1):.1f}%)" if h2_avail > 0 else "N/A"

        if 'ki67' in c.columns and c['ki67'].notna().sum() > 10:
            row['Ki67 median (IQR)'] = f"{c['ki67'].median():.0f} ({c['ki67'].quantile(0.25):.0f}-{c['ki67'].quantile(0.75):.0f})"
        else:
            row['Ki67 median (IQR)'] = 'N/A'

        if 'grade' in c.columns and c['grade'].notna().sum() > 10:
            g_avail = c['grade'].notna().sum()
            for g in [1, 2, 3]:
                ng = (c['grade'] == g).sum()
                row[f'Grade {g}'] = f"{ng} ({100*ng/g_avail:.1f}%)"
        else:
            for g in [1, 2, 3]:
                row[f'Grade {g}'] = 'N/A'

        if 'age' in c.columns and c['age'].notna().sum() > 10:
            row['Age median (IQR)'] = f"{c['age'].median():.0f} ({c['age'].quantile(0.25):.0f}-{c['age'].quantile(0.75):.0f})"
        else:
            row['Age median (IQR)'] = 'N/A'

        rows.append(row)

    t1 = pd.DataFrame(rows)
    t1.to_csv(os.path.join(TAB_DIR, 'table1_cohort_characteristics.csv'), index=False)


def table2_performance(results):
    print("  Table 2: Performance metrics")
    if not results:
        return
    rdf = pd.DataFrame(results.values()).round(3)
    rdf.to_csv(os.path.join(TAB_DIR, 'table2_performance_metrics.csv'), index=False)


def table3_perclass(predictions, le):
    print("  Table 3: Per-class metrics")
    rows = []
    for key, pred in predictions.items():
        set_name, model_name, cohort = key
        y_true, y_pred = pred['y_true'], pred['y_pred']
        report = classification_report(y_true, y_pred, target_names=PAM50_ORDER,
                                       output_dict=True, zero_division=0)
        for subtype in PAM50_ORDER:
            if subtype in report:
                rows.append({
                    'Feature Set': set_name, 'Model': model_name, 'Cohort': cohort,
                    'PAM50 Subtype': subtype,
                    'Precision': round(report[subtype]['precision'], 3),
                    'Recall': round(report[subtype]['recall'], 3),
                    'F1': round(report[subtype]['f1-score'], 3),
                    'Support': report[subtype]['support'],
                })
    t3 = pd.DataFrame(rows)
    t3.to_csv(os.path.join(TAB_DIR, 'table3_perclass_metrics.csv'), index=False)


def table4_missing(df):
    print("  Table 4: Missing data")
    key_vars = ['er_status', 'pr_status', 'her2_status', 'ki67', 'grade', 'age', 'pam50_label']
    available_vars = [v for v in key_vars if v in df.columns]
    rows = []
    for cohort in ['GSE81538', 'GSE96058', 'TCGA-BRCA', 'METABRIC']:
        c = df[df['cohort'] == cohort]
        n = len(c)
        if n == 0:
            continue
        row = {'Cohort': cohort, 'N': n}
        for var in available_vars:
            nm = c[var].isna().sum()
            row[f'{var} missing'] = f"{nm} ({100*nm/n:.1f}%)"
        rows.append(row)
    t4 = pd.DataFrame(rows)
    t4.to_csv(os.path.join(TAB_DIR, 'table4_missing_data.csv'), index=False)


# ============================================================
# SENSITIVITY ANALYSES (Phase 9)
# ============================================================

def sensitivity_analyses(df, le):
    print("\n" + "=" * 60)
    print("PHASE 9: SENSITIVITY ANALYSES")
    print("=" * 60)

    train_cohorts = ['GSE81538', 'GSE96058']
    features = ['er_binary', 'pr_binary', 'her2_binary']
    results_sens = []

    # Base case: 4-class
    base_result = run_model_eval(df, features, train_cohorts, le, 'Base (4-class)')
    results_sens.extend(base_result)

    # Sensitivity 1: Luminal A+B grouped → "Luminal" vs Her2 vs Basal (3-class)
    df_3class = df.copy()
    df_3class['pam50_3class'] = df_3class['pam50_label'].replace({'LumA': 'Luminal', 'LumB': 'Luminal'})
    le3 = LabelEncoder()
    le3.fit(['Basal', 'Her2', 'Luminal'])
    for r in run_model_eval(df_3class, features, train_cohorts, le3, 'Luminal grouped (3-class)', label_col='pam50_3class'):
        results_sens.append(r)

    # Sensitivity 2: RNA-seq only cohorts
    df_rna = df[df['platform'] == 'RNA-seq'].copy()
    for r in run_model_eval(df_rna, features, train_cohorts, le, 'RNA-seq only'):
        results_sens.append(r)

    sens_df = pd.DataFrame(results_sens)
    sens_df.to_csv(os.path.join(TAB_DIR, 'table5_sensitivity_analyses.csv'), index=False)
    print(f"  Saved sensitivity results: {sens_df.shape}")
    print(sens_df.to_string(index=False))


def run_model_eval(df, features, train_cohorts, le, analysis_name, label_col='pam50_label'):
    """Run a single model evaluation for sensitivity analysis."""
    classes = list(le.classes_)
    results = []

    train_mask = df['cohort'].isin(train_cohorts) & df[label_col].isin(classes)
    train_data = df.loc[train_mask].dropna(subset=features + [label_col])

    if len(train_data) < 30:
        return results

    X_train = train_data[features].values.astype(float)
    y_train = le.transform(train_data[label_col])

    model = xgb.XGBClassifier(
        n_estimators=300, max_depth=5, learning_rate=0.1,
        objective='multi:softprob', num_class=len(classes),
        eval_metric='mlogloss', random_state=42, verbosity=0
    )
    model.fit(X_train, y_train)

    for cohort in df['cohort'].unique():
        if cohort in train_cohorts:
            continue
        val_mask = (df['cohort'] == cohort) & df[label_col].isin(classes)
        val_data = df.loc[val_mask].dropna(subset=features + [label_col])
        if len(val_data) < 20:
            continue
        X_val = val_data[features].values.astype(float)
        y_val = le.transform(val_data[label_col])
        y_pred = model.predict(X_val)

        results.append({
            'Analysis': analysis_name, 'Cohort': cohort, 'N': len(val_data),
            'Macro F1': round(f1_score(y_val, y_pred, average='macro'), 3),
            'Kappa': round(cohen_kappa_score(y_val, y_pred), 3),
            'Balanced Accuracy': round(balanced_accuracy_score(y_val, y_pred), 3),
        })

    return results


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    df = build_harmonized_dataset()
    df_target = define_target(df)
    df_target = create_ihq_surrogate(df_target)
    df_target, feature_sets = prepare_features(df_target)
    results, predictions, models, scaler, le = train_and_evaluate(df_target, feature_sets)

    generate_figures(df_target, results, predictions, le)
    generate_tables(df_target, results, predictions, le)
    sensitivity_analyses(df_target, le)

    # Summary
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    if results:
        rdf = pd.DataFrame(results.values())
        # Show best results per cohort
        for cohort in rdf['validation_cohort'].unique():
            cdf = rdf[rdf['validation_cohort'] == cohort]
            best = cdf.loc[cdf['macro_f1'].idxmax()]
            print(f"\n  {cohort} (best): {best['model']} ({best['feature_set']})")
            print(f"    F1={best['macro_f1']:.3f}, κ={best['kappa']:.3f}, BA={best['balanced_accuracy']:.3f}")

    print(f"\nOutputs: {FIG_DIR}, {TAB_DIR}")
