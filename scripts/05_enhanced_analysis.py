"""
Enhanced analysis: bootstrap CIs, head-to-head fair comparison,
grey zone / confidence score, calibration, improved figures.
"""

import os, sys, warnings
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
    f1_score, cohen_kappa_score, accuracy_score, brier_score_loss
)
from sklearn.calibration import calibration_curve
import xgboost as xgb

warnings.filterwarnings('ignore')
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC_DIR = os.path.join(BASE_DIR, "data", "processed")
FIG_DIR = os.path.join(BASE_DIR, "figures")
TAB_DIR = os.path.join(BASE_DIR, "tables")

PAM50_ORDER = ['Basal', 'Her2', 'LumA', 'LumB']
PAM50_COLORS = {'Basal': '#CC79A7', 'Her2': '#D55E00', 'LumA': '#0072B2', 'LumB': '#56B4E9'}
PAM50_LABELS = {'Basal': 'Basal-like', 'Her2': 'HER2-enriched', 'LumA': 'Luminal A', 'LumB': 'Luminal B'}

# Publication-quality settings
plt.rcParams.update({
    'figure.dpi': 300, 'savefig.dpi': 300, 'savefig.bbox': 'tight',
    'font.size': 9, 'font.family': 'sans-serif',
    'axes.titlesize': 11, 'axes.labelsize': 10,
    'xtick.labelsize': 8, 'ytick.labelsize': 8,
    'legend.fontsize': 8, 'figure.facecolor': 'white',
    'axes.spines.top': False, 'axes.spines.right': False,
})


def load_data():
    df = pd.read_csv(os.path.join(PROC_DIR, "harmonized_full.csv"))
    # Filter 4-class
    df = df[df['pam50_label'].isin(PAM50_ORDER)].copy()
    # Ensure features
    df['er_binary'] = (df['er_status'] == 'Positive').astype(float)
    df['pr_binary'] = (df['pr_status'] == 'Positive').astype(float)
    df['her2_binary'] = (df['her2_status'] == 'Positive').astype(float)
    df.loc[df['er_status'].isna(), 'er_binary'] = np.nan
    df.loc[df['pr_status'].isna(), 'pr_binary'] = np.nan
    df.loc[df['her2_status'].isna(), 'her2_binary'] = np.nan

    if 'ki67' not in df.columns:
        df['ki67'] = np.nan
    if 'ki67_high' in df.columns:
        mask = df['ki67'].isna() & df['ki67_high'].notna()
        df.loc[mask & (df['ki67_high'] == True), 'ki67'] = 30.0
        df.loc[mask & (df['ki67_high'] == False), 'ki67'] = 10.0

    # IHQ surrogate
    df['hr_pos'] = (df['er_status'] == 'Positive') | (df['pr_status'] == 'Positive')
    df['hr_neg'] = (df['er_status'] == 'Negative') & (df['pr_status'] == 'Negative')

    df['_ki67_high'] = np.nan
    if 'ki67' in df.columns:
        m = df['ki67'].notna()
        df.loc[m, '_ki67_high'] = (df.loc[m, 'ki67'] >= 20)
    if 'grade' in df.columns:
        m2 = df['_ki67_high'].isna() & df['grade'].notna()
        df.loc[m2 & (df['grade'] == 3), '_ki67_high'] = True
        df.loc[m2 & (df['grade'].isin([1, 2])), '_ki67_high'] = False

    tn = df['hr_neg'] & (df['her2_status'] == 'Negative')
    h2p = df['hr_neg'] & (df['her2_status'] == 'Positive')
    lbh = df['hr_pos'] & (df['her2_status'] == 'Positive')
    lbn = df['hr_pos'] & (df['her2_status'] == 'Negative') & (df['_ki67_high'] == True)
    la = df['hr_pos'] & (df['her2_status'] == 'Negative') & (df['_ki67_high'] == False)

    df['ihq_as_pam50'] = np.nan
    df.loc[tn, 'ihq_as_pam50'] = 'Basal'
    df.loc[h2p, 'ihq_as_pam50'] = 'Her2'
    df.loc[lbh, 'ihq_as_pam50'] = 'LumB'
    df.loc[lbn, 'ihq_as_pam50'] = 'LumB'
    df.loc[la, 'ihq_as_pam50'] = 'LumA'

    return df


def bootstrap_metrics(y_true, y_pred, n_boot=1000, seed=42):
    """Bootstrap 95% CI for macro-F1, kappa, balanced accuracy."""
    rng = np.random.RandomState(seed)
    n = len(y_true)
    f1s, kappas, bas = [], [], []
    for _ in range(n_boot):
        idx = rng.choice(n, n, replace=True)
        yt, yp = y_true[idx], y_pred[idx]
        if len(np.unique(yt)) < 2:
            continue
        f1s.append(f1_score(yt, yp, average='macro', zero_division=0))
        kappas.append(cohen_kappa_score(yt, yp))
        bas.append(balanced_accuracy_score(yt, yp))
    return {
        'f1_mean': np.mean(f1s), 'f1_lo': np.percentile(f1s, 2.5), 'f1_hi': np.percentile(f1s, 97.5),
        'kappa_mean': np.mean(kappas), 'kappa_lo': np.percentile(kappas, 2.5), 'kappa_hi': np.percentile(kappas, 97.5),
        'ba_mean': np.mean(bas), 'ba_lo': np.percentile(bas, 2.5), 'ba_hi': np.percentile(bas, 97.5),
    }


def run_full_analysis():
    print("Loading data...")
    df = load_data()
    le = LabelEncoder()
    le.fit(PAM50_ORDER)

    train_cohorts = ['GSE81538', 'GSE96058']
    features_set1 = ['er_binary', 'pr_binary', 'her2_binary']
    features_set2 = ['er_binary', 'pr_binary', 'her2_binary', 'grade']
    features_set3 = ['er_binary', 'pr_binary', 'her2_binary', 'ki67', 'grade']

    # ========== N FLOW TABLE ==========
    print("\n=== SAMPLE FLOW ===")
    flow_rows = []
    for cohort in ['GSE81538', 'GSE96058', 'TCGA-BRCA', 'METABRIC']:
        c = df[df['cohort'] == cohort]
        n_4class = len(c)
        n_set1 = c.dropna(subset=features_set1).shape[0]
        n_set2 = c.dropna(subset=features_set2).shape[0]
        n_surr = c['ihq_as_pam50'].notna().sum()
        n_both = c.dropna(subset=features_set1)[c.dropna(subset=features_set1)['ihq_as_pam50'].notna()].shape[0]
        flow_rows.append({
            'Cohort': cohort, 'N (4-class PAM50)': n_4class,
            'N (Set 1 complete)': n_set1, 'N (Set 2 complete)': n_set2,
            'N (Surrogate classifiable)': n_surr,
            'N (Head-to-head Set 1 vs Surrogate)': n_both,
        })
        print(f"  {cohort}: 4-class={n_4class}, Set1={n_set1}, Set2={n_set2}, Surr={n_surr}, H2H={n_both}")

    flow_df = pd.DataFrame(flow_rows)
    flow_df.to_csv(os.path.join(TAB_DIR, 'table_sample_flow.csv'), index=False)

    # ========== TRAIN MODELS ==========
    print("\n=== TRAINING ===")
    all_results = []

    for set_name, features in [('Set 1', features_set1), ('Set 2', features_set2), ('Set 3', features_set3)]:
        train_mask = df['cohort'].isin(train_cohorts)
        train_data = df.loc[train_mask].dropna(subset=features + ['pam50_label'])
        if len(train_data) < 50:
            print(f"  {set_name}: too few ({len(train_data)})")
            continue

        X_train = train_data[features].values.astype(float)
        y_train = le.transform(train_data['pam50_label'])
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_train)

        models = {
            'Logistic Regression': LogisticRegression(solver='lbfgs', max_iter=2000, C=1.0, class_weight='balanced'),
            'Random Forest': RandomForestClassifier(n_estimators=500, class_weight='balanced', random_state=42, n_jobs=-1),
            'XGBoost': xgb.XGBClassifier(n_estimators=500, max_depth=6, learning_rate=0.1,
                                          objective='multi:softprob', num_class=4,
                                          eval_metric='mlogloss', random_state=42, verbosity=0),
        }

        fitted = {}
        for mname, model in models.items():
            Xin = X_scaled if 'Logistic' in mname else X_train
            model.fit(Xin, y_train)
            fitted[mname] = model

        # Evaluate on each external cohort
        for cohort in ['TCGA-BRCA', 'METABRIC']:
            val_data = df[df['cohort'] == cohort].dropna(subset=features + ['pam50_label'])
            if len(val_data) < 20:
                continue

            X_val = val_data[features].values.astype(float)
            y_val = le.transform(val_data['pam50_label'])
            X_val_s = scaler.transform(X_val)

            for mname, model in fitted.items():
                Xin = X_val_s if 'Logistic' in mname else X_val
                y_pred = model.predict(Xin)
                y_prob = model.predict_proba(Xin)

                boot = bootstrap_metrics(y_val, y_pred)
                all_results.append({
                    'Feature Set': set_name, 'Model': mname, 'Cohort': cohort, 'N': len(val_data),
                    'Macro F1': f"{boot['f1_mean']:.3f}", 'F1 95% CI': f"({boot['f1_lo']:.3f}-{boot['f1_hi']:.3f})",
                    'Kappa': f"{boot['kappa_mean']:.3f}", 'Kappa 95% CI': f"({boot['kappa_lo']:.3f}-{boot['kappa_hi']:.3f})",
                    'Balanced Acc': f"{boot['ba_mean']:.3f}", 'BA 95% CI': f"({boot['ba_lo']:.3f}-{boot['ba_hi']:.3f})",
                    '_f1': boot['f1_mean'], '_f1_lo': boot['f1_lo'], '_f1_hi': boot['f1_hi'],
                    '_kappa': boot['kappa_mean'], '_ba': boot['ba_mean'],
                    '_y_true': y_val, '_y_pred': y_pred, '_y_prob': y_prob,
                })
                print(f"  {set_name} | {mname} | {cohort}: F1={boot['f1_mean']:.3f} ({boot['f1_lo']:.3f}-{boot['f1_hi']:.3f})")

            # HEAD-TO-HEAD: same N for surrogate and ML
            h2h_data = val_data[val_data['ihq_as_pam50'].isin(PAM50_ORDER)]
            if len(h2h_data) >= 20:
                X_h2h = h2h_data[features].values.astype(float)
                y_h2h = le.transform(h2h_data['pam50_label'])
                y_surr = le.transform(h2h_data['ihq_as_pam50'])
                X_h2h_s = scaler.transform(X_h2h)

                # Surrogate on this exact subset
                boot_s = bootstrap_metrics(y_h2h, y_surr)
                all_results.append({
                    'Feature Set': set_name, 'Model': 'IHQ Surrogate (H2H)', 'Cohort': cohort, 'N': len(h2h_data),
                    'Macro F1': f"{boot_s['f1_mean']:.3f}", 'F1 95% CI': f"({boot_s['f1_lo']:.3f}-{boot_s['f1_hi']:.3f})",
                    'Kappa': f"{boot_s['kappa_mean']:.3f}", 'Kappa 95% CI': f"({boot_s['kappa_lo']:.3f}-{boot_s['kappa_hi']:.3f})",
                    'Balanced Acc': f"{boot_s['ba_mean']:.3f}", 'BA 95% CI': f"({boot_s['ba_lo']:.3f}-{boot_s['ba_hi']:.3f})",
                    '_f1': boot_s['f1_mean'], '_f1_lo': boot_s['f1_lo'], '_f1_hi': boot_s['f1_hi'],
                    '_kappa': boot_s['kappa_mean'], '_ba': boot_s['ba_mean'],
                    '_y_true': y_h2h, '_y_pred': y_surr, '_y_prob': None,
                })

                # Best ML on this exact subset
                best_ml_name = max(fitted.keys(), key=lambda m: f1_score(y_h2h,
                    fitted[m].predict(X_h2h_s if 'Logistic' in m else X_h2h), average='macro'))
                Xin = X_h2h_s if 'Logistic' in best_ml_name else X_h2h
                y_ml_h2h = fitted[best_ml_name].predict(Xin)
                boot_ml = bootstrap_metrics(y_h2h, y_ml_h2h)
                all_results.append({
                    'Feature Set': set_name, 'Model': f'{best_ml_name} (H2H)', 'Cohort': cohort, 'N': len(h2h_data),
                    'Macro F1': f"{boot_ml['f1_mean']:.3f}", 'F1 95% CI': f"({boot_ml['f1_lo']:.3f}-{boot_ml['f1_hi']:.3f})",
                    'Kappa': f"{boot_ml['kappa_mean']:.3f}", 'Kappa 95% CI': f"({boot_ml['kappa_lo']:.3f}-{boot_ml['kappa_hi']:.3f})",
                    'Balanced Acc': f"{boot_ml['ba_mean']:.3f}", 'BA 95% CI': f"({boot_ml['ba_lo']:.3f}-{boot_ml['ba_hi']:.3f})",
                    '_f1': boot_ml['f1_mean'], '_f1_lo': boot_ml['f1_lo'], '_f1_hi': boot_ml['f1_hi'],
                    '_kappa': boot_ml['kappa_mean'], '_ba': boot_ml['ba_mean'],
                    '_y_true': y_h2h, '_y_pred': y_ml_h2h, '_y_prob': None,
                })
                print(f"  {set_name} | H2H {cohort} (N={len(h2h_data)}): Surr F1={boot_s['f1_mean']:.3f}, {best_ml_name} F1={boot_ml['f1_mean']:.3f}")

    # ========== LUMINAL A/B DISCORDANCE TABLE ==========
    print("\n=== LUMINAL A/B DISCORDANCE ===")
    disc_rows = []
    for cohort in ['GSE81538', 'GSE96058', 'TCGA-BRCA', 'METABRIC']:
        c = df[(df['cohort'] == cohort) & df['ihq_as_pam50'].isin(PAM50_ORDER) & df['pam50_label'].isin(PAM50_ORDER)]
        if len(c) < 20:
            continue

        for true_sub in PAM50_ORDER:
            mask = c['pam50_label'] == true_sub
            n_true = mask.sum()
            if n_true == 0:
                continue
            for pred_sub in PAM50_ORDER:
                n_pred = (c.loc[mask, 'ihq_as_pam50'] == pred_sub).sum()
                if n_pred > 0:
                    disc_rows.append({
                        'Cohort': cohort, 'True PAM50': true_sub,
                        'IHQ Surrogate': pred_sub, 'N': n_pred,
                        'Rate': f"{n_pred/n_true:.1%}",
                    })
    disc_df = pd.DataFrame(disc_rows)
    disc_df.to_csv(os.path.join(TAB_DIR, 'table_luminal_discordance.csv'), index=False)

    # Focused LumA/LumB confusion
    print("\n  LumA/LumB confusion by cohort:")
    lum_rows = []
    for cohort in ['GSE81538', 'GSE96058', 'TCGA-BRCA', 'METABRIC']:
        c = df[(df['cohort'] == cohort) & df['ihq_as_pam50'].isin(PAM50_ORDER) & df['pam50_label'].isin(['LumA', 'LumB'])]
        if len(c) < 10:
            continue
        lumA_true = c[c['pam50_label'] == 'LumA']
        lumB_true = c[c['pam50_label'] == 'LumB']
        a_as_b = (lumA_true['ihq_as_pam50'] == 'LumB').sum()
        b_as_a = (lumB_true['ihq_as_pam50'] == 'LumA').sum()
        lum_rows.append({
            'Cohort': cohort,
            'True LumA (N)': len(lumA_true), 'LumA misclassified as LumB': f"{a_as_b} ({100*a_as_b/max(len(lumA_true),1):.1f}%)",
            'True LumB (N)': len(lumB_true), 'LumB misclassified as LumA': f"{b_as_a} ({100*b_as_a/max(len(lumB_true),1):.1f}%)",
        })
        print(f"    {cohort}: LumA->LumB={a_as_b}/{len(lumA_true)} ({100*a_as_b/max(len(lumA_true),1):.1f}%), "
              f"LumB->LumA={b_as_a}/{len(lumB_true)} ({100*b_as_a/max(len(lumB_true),1):.1f}%)")

    lum_df = pd.DataFrame(lum_rows)
    lum_df.to_csv(os.path.join(TAB_DIR, 'table_lumAB_crossover.csv'), index=False)

    # ========== GREY ZONE / CONFIDENCE SCORE ==========
    print("\n=== GREY ZONE ANALYSIS ===")
    # Use XGBoost Set 2 on METABRIC
    features_gz = features_set2
    train_data_gz = df[df['cohort'].isin(train_cohorts)].dropna(subset=features_gz + ['pam50_label'])
    X_gz = train_data_gz[features_gz].values.astype(float)
    y_gz = le.transform(train_data_gz['pam50_label'])

    xgb_gz = xgb.XGBClassifier(n_estimators=500, max_depth=6, learning_rate=0.1,
                                 objective='multi:softprob', num_class=4,
                                 eval_metric='mlogloss', random_state=42, verbosity=0)
    xgb_gz.fit(X_gz, y_gz)

    for cohort in ['METABRIC']:
        val_gz = df[df['cohort'] == cohort].dropna(subset=features_gz + ['pam50_label'])
        if len(val_gz) < 20:
            continue
        X_vgz = val_gz[features_gz].values.astype(float)
        y_vgz = le.transform(val_gz['pam50_label'])
        probs = xgb_gz.predict_proba(X_vgz)
        max_prob = probs.max(axis=1)
        y_pred_gz = xgb_gz.predict(X_vgz)

        # Define confidence zones
        val_gz = val_gz.copy()
        val_gz['max_prob'] = max_prob
        val_gz['correct'] = (y_pred_gz == y_vgz)
        val_gz['predicted'] = le.inverse_transform(y_pred_gz)

        # Terciles of max_prob
        thresholds = [0.0, 0.5, 0.7, 1.01]
        zone_labels = ['Low (<0.50)', 'Medium (0.50-0.70)', 'High (>0.70)']
        gz_rows = []
        for i, (lo, hi, label) in enumerate(zip(thresholds[:-1], thresholds[1:], zone_labels)):
            mask = (max_prob >= lo) & (max_prob < hi)
            n_zone = mask.sum()
            if n_zone == 0:
                continue
            acc_zone = val_gz.loc[val_gz.index[mask], 'correct'].mean()
            # Surrogate accuracy in this zone
            surr_data = val_gz.iloc[np.where(mask)[0]]
            surr_data = surr_data[surr_data['ihq_as_pam50'].isin(PAM50_ORDER)]
            surr_acc = (surr_data['ihq_as_pam50'] == surr_data['pam50_label']).mean() if len(surr_data) > 0 else np.nan
            # LumA/LumB proportion
            lum_prop = ((val_gz.iloc[np.where(mask)[0]]['pam50_label'].isin(['LumA', 'LumB'])).mean())
            gz_rows.append({
                'Confidence Zone': label, 'N': n_zone, f'N (%)': f"{n_zone} ({100*n_zone/len(val_gz):.1f}%)",
                'ML Accuracy': f"{acc_zone:.3f}", 'Surrogate Accuracy': f"{surr_acc:.3f}" if pd.notna(surr_acc) else 'N/A',
                'Luminal A+B proportion': f"{lum_prop:.1%}",
            })
            print(f"  {label}: N={n_zone}, ML acc={acc_zone:.3f}, Surr acc={surr_acc:.3f}, Luminal={lum_prop:.1%}")

        gz_df = pd.DataFrame(gz_rows)
        gz_df.to_csv(os.path.join(TAB_DIR, 'table_grey_zone.csv'), index=False)

    # ========== SENSITIVITY: 3-class ==========
    print("\n=== 3-CLASS SENSITIVITY ===")
    df_3c = df.copy()
    df_3c['pam50_3c'] = df_3c['pam50_label'].replace({'LumA': 'Luminal', 'LumB': 'Luminal'})
    le3 = LabelEncoder()
    le3.fit(['Basal', 'Her2', 'Luminal'])

    train_3c = df_3c[df_3c['cohort'].isin(train_cohorts)].dropna(subset=features_set1 + ['pam50_3c'])
    X3 = train_3c[features_set1].values.astype(float)
    y3 = le3.transform(train_3c['pam50_3c'])
    xgb3 = xgb.XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.1,
                               objective='multi:softprob', num_class=3,
                               eval_metric='mlogloss', random_state=42, verbosity=0)
    xgb3.fit(X3, y3)

    sens_rows = []
    for cohort in ['TCGA-BRCA', 'METABRIC']:
        vc = df_3c[df_3c['cohort'] == cohort].dropna(subset=features_set1 + ['pam50_3c'])
        if len(vc) < 20:
            continue
        Xv = vc[features_set1].values.astype(float)
        yv = le3.transform(vc['pam50_3c'])
        yp = xgb3.predict(Xv)
        boot = bootstrap_metrics(yv, yp)
        sens_rows.append({
            'Analysis': '3-class (Luminal grouped)', 'Cohort': cohort, 'N': len(vc),
            'Macro F1': f"{boot['f1_mean']:.3f}", 'F1 95% CI': f"({boot['f1_lo']:.3f}-{boot['f1_hi']:.3f})",
            'Kappa': f"{boot['kappa_mean']:.3f}",
        })
        print(f"  3-class {cohort}: F1={boot['f1_mean']:.3f} ({boot['f1_lo']:.3f}-{boot['f1_hi']:.3f})")

    # 4-class for comparison
    for cohort in ['TCGA-BRCA', 'METABRIC']:
        vc = df[df['cohort'] == cohort].dropna(subset=features_set1 + ['pam50_label'])
        if len(vc) < 20:
            continue

        train_4 = df[df['cohort'].isin(train_cohorts)].dropna(subset=features_set1 + ['pam50_label'])
        X4t = train_4[features_set1].values.astype(float)
        y4t = le.transform(train_4['pam50_label'])
        xgb4 = xgb.XGBClassifier(n_estimators=300, max_depth=5, learning_rate=0.1,
                                   objective='multi:softprob', num_class=4,
                                   eval_metric='mlogloss', random_state=42, verbosity=0)
        xgb4.fit(X4t, y4t)
        Xv = vc[features_set1].values.astype(float)
        yv = le.transform(vc['pam50_label'])
        yp = xgb4.predict(Xv)
        boot = bootstrap_metrics(yv, yp)
        sens_rows.append({
            'Analysis': '4-class (primary)', 'Cohort': cohort, 'N': len(vc),
            'Macro F1': f"{boot['f1_mean']:.3f}", 'F1 95% CI': f"({boot['f1_lo']:.3f}-{boot['f1_hi']:.3f})",
            'Kappa': f"{boot['kappa_mean']:.3f}",
        })

    sens_df = pd.DataFrame(sens_rows)
    sens_df.to_csv(os.path.join(TAB_DIR, 'table_sensitivity_enhanced.csv'), index=False)

    # Save main results
    results_df = pd.DataFrame([{k: v for k, v in r.items() if not k.startswith('_')} for r in all_results])
    results_df.to_csv(os.path.join(TAB_DIR, 'table_main_results.csv'), index=False)

    return df, all_results, le


# ============================================================
# PUBLICATION FIGURES
# ============================================================

def generate_pub_figures(df, results, le):
    print("\n=== GENERATING PUBLICATION FIGURES ===")

    # ---- FIGURE 1: CONSORT-style flow ----
    fig1_flow(df)

    # ---- FIGURE 2: Cohort comparison (multi-panel) ----
    fig2_cohort(df)

    # ---- FIGURE 3: Head-to-head forest plot ----
    fig3_forest(results)

    # ---- FIGURE 4: Confusion matrices (key comparisons) ----
    fig4_confusion(df, results, le)

    # ---- FIGURE 5: Grey zone / confidence ----
    fig5_greyzone(df, le)

    # ---- FIGURE 6: Feature importance ----
    fig6_importance(df, le)


def fig1_flow(df):
    """CONSORT-like flow diagram."""
    print("  Fig 1: Flow diagram")
    fig, ax = plt.subplots(figsize=(10, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis('off')

    def box(x, y, text, color='#E8F5E9', w=3.2, h=1.2):
        rect = plt.Rectangle((x - w/2, y - h/2), w, h, linewidth=1.2,
                              edgecolor='#555', facecolor=color, zorder=2)
        ax.add_patch(rect)
        ax.text(x, y, text, ha='center', va='center', fontsize=8, zorder=3)

    def arrow(x1, y1, x2, y2):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', lw=1.2, color='#555'), zorder=1)

    # Title
    ax.text(5, 13.5, 'Figure 1. Study Design and Sample Flow', fontsize=11, fontweight='bold', ha='center')

    # Source databases
    box(2.5, 12, 'NCBI GEO\n(GSE81538 + GSE96058)', '#E8F5E9', 3.5, 1)
    box(7.5, 12, 'cBioPortal\n(TCGA-BRCA + METABRIC)', '#E3F2FD', 3.5, 1)

    # Raw cohorts
    n1 = len(df[df['cohort'] == 'GSE81538'])
    n2 = len(df[df['cohort'] == 'GSE96058'])
    n3 = len(df[df['cohort'] == 'TCGA-BRCA'])
    n4 = len(df[df['cohort'] == 'METABRIC'])

    box(1.5, 10, f'GSE81538\nn = {n1}', '#C8E6C9', 2.5, 0.9)
    box(4, 10, f'GSE96058\nn = {n2}', '#C8E6C9', 2.5, 0.9)
    box(6.5, 10, f'TCGA-BRCA\nn = {n3}', '#BBDEFB', 2.5, 0.9)
    box(9, 10, f'METABRIC\nn = {n4}', '#BBDEFB', 2.5, 0.9)

    arrow(2.5, 11.5, 1.5, 10.5)
    arrow(2.5, 11.5, 4, 10.5)
    arrow(7.5, 11.5, 6.5, 10.5)
    arrow(7.5, 11.5, 9, 10.5)

    # Exclusion
    box(5, 8.5, 'Excluded: Normal-like, Claudin-low,\nmissing PAM50 labels', '#FFF9C4', 4, 0.8)
    arrow(3, 9.5, 5, 8.9)
    arrow(7.5, 9.5, 5, 8.9)

    # 4-class PAM50
    n_train = n1 + n2
    n_val = n3 + n4
    box(2.5, 7, f'Training Set\nn = {n_train}\n(4-class PAM50)', '#A5D6A7', 3.5, 1.2)
    box(7.5, 7, f'Validation Set\nn = {n_val}\n(4-class PAM50)', '#90CAF9', 3.5, 1.2)

    arrow(5, 8.1, 2.5, 7.6)
    arrow(5, 8.1, 7.5, 7.6)

    # Analysis
    box(2.5, 5, 'Feature Sets\nSet 1: ER, PR, HER2\nSet 2: + Grade\nSet 3: + Ki67, Grade', '#FFF3E0', 3.5, 1.5)
    box(7.5, 5, 'Models\nLogistic Regression\nRandom Forest\nXGBoost\nvs IHQ Surrogate', '#FFF3E0', 3.5, 1.5)

    arrow(2.5, 6.4, 2.5, 5.8)
    arrow(7.5, 6.4, 7.5, 5.8)
    ax.annotate('', xy=(7.5, 5.8), xytext=(2.5, 5.8),
                arrowprops=dict(arrowstyle='<->', lw=1, color='#999', linestyle='--'))

    # Primary endpoint
    box(5, 3, 'Primary Endpoint\nMacro F1-Score (4-class PAM50)\nwith Bootstrap 95% CI', '#FCE4EC', 5, 1)
    arrow(2.5, 4.2, 5, 3.5)
    arrow(7.5, 4.2, 5, 3.5)

    # Secondary
    box(5, 1.5, 'Secondary: Cohen\'s \u03BA | Balanced Accuracy | Per-class Sensitivity\n'
                'Exploratory: Grey Zone Analysis | 3-class Sensitivity | LumA/LumB Crossover',
        '#F3E5F5', 6, 0.9)
    arrow(5, 2.5, 5, 2)

    plt.savefig(os.path.join(FIG_DIR, 'fig1_flow.png'), bbox_inches='tight')
    plt.close()


def fig2_cohort(df):
    """Multi-panel cohort characteristics."""
    print("  Fig 2: Cohort characteristics")
    fig = plt.figure(figsize=(7.5, 9))  # Journal single-column width
    gs = gridspec.GridSpec(3, 2, hspace=0.45, wspace=0.35)

    cohort_order = ['GSE81538', 'GSE96058', 'TCGA-BRCA', 'METABRIC']
    cohort_colors = {'GSE81538': '#66BB6A', 'GSE96058': '#43A047', 'TCGA-BRCA': '#42A5F5', 'METABRIC': '#1E88E5'}

    # A: PAM50 distribution
    ax = fig.add_subplot(gs[0, 0])
    ct = pd.crosstab(df['cohort'], df['pam50_label'], normalize='index').reindex(
        index=cohort_order, columns=PAM50_ORDER, fill_value=0)
    ct.plot(kind='barh', stacked=True, ax=ax, color=[PAM50_COLORS[s] for s in PAM50_ORDER], width=0.7)
    ax.set_xlabel('Proportion')
    ax.set_title('A. PAM50 Subtype Distribution', fontsize=10, fontweight='bold', loc='left')
    ax.legend(title='', fontsize=7, loc='lower right')

    # B: ER/HER2 status
    ax = fig.add_subplot(gs[0, 1])
    er_pos = df.groupby('cohort')['er_status'].apply(lambda x: (x == 'Positive').mean()).reindex(cohort_order)
    h2_pos = df.groupby('cohort')['her2_status'].apply(lambda x: (x == 'Positive').mean()).reindex(cohort_order)
    x = np.arange(len(cohort_order))
    ax.bar(x - 0.15, er_pos.values, 0.3, label='ER+', color='#4CAF50', alpha=0.8)
    ax.bar(x + 0.15, h2_pos.values, 0.3, label='HER2+', color='#FF7043', alpha=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(cohort_order, rotation=45, ha='right')
    ax.set_ylabel('Proportion Positive')
    ax.set_title('B. ER and HER2 Positivity', fontsize=10, fontweight='bold', loc='left')
    ax.legend(fontsize=7)
    ax.set_ylim(0, 1)

    # C: Grade
    ax = fig.add_subplot(gs[1, 0])
    df_g = df.dropna(subset=['grade'])
    if len(df_g) > 0:
        ct_g = pd.crosstab(df_g['cohort'], df_g['grade'], normalize='index').reindex(
            index=[c for c in cohort_order if c in df_g['cohort'].unique()], fill_value=0)
        ct_g.plot(kind='barh', stacked=True, ax=ax,
                  color=['#81C784', '#FFD54F', '#E57373'], width=0.7)
        ax.set_xlabel('Proportion')
        ax.set_title('C. Histologic Grade', fontsize=10, fontweight='bold', loc='left')
        ax.legend(title='Grade', fontsize=7, loc='lower right')

    # D: Ki67 by PAM50 (GSE81538)
    ax = fig.add_subplot(gs[1, 1])
    df_ki = df[(df['cohort'] == 'GSE81538') & df['ki67'].notna()]
    if len(df_ki) > 0:
        for sub in PAM50_ORDER:
            vals = df_ki[df_ki['pam50_label'] == sub]['ki67']
            if len(vals) > 0:
                ax.hist(vals, bins=15, alpha=0.55, label=PAM50_LABELS[sub], color=PAM50_COLORS[sub], density=True)
        ax.axvline(x=20, color='red', linestyle='--', alpha=0.7, linewidth=0.8)
        ax.text(21, ax.get_ylim()[1] * 0.9, '20%', color='red', fontsize=7)
        ax.set_xlabel('Ki-67 (%)')
        ax.set_ylabel('Density')
        ax.set_title('D. Ki-67 by Subtype (GSE81538)', fontsize=10, fontweight='bold', loc='left')
        ax.legend(fontsize=6)

    # E: Sample sizes
    ax = fig.add_subplot(gs[2, 0])
    ns = df.groupby('cohort').size().reindex(cohort_order)
    bars = ax.barh(cohort_order, ns.values, color=[cohort_colors[c] for c in cohort_order], height=0.6)
    for bar, v in zip(bars, ns.values):
        ax.text(v + 30, bar.get_y() + bar.get_height()/2, f'n={v}', va='center', fontsize=8)
    ax.set_xlabel('Number of Samples')
    ax.set_title('E. Sample Size (4-class)', fontsize=10, fontweight='bold', loc='left')

    # F: Missing data heatmap
    ax = fig.add_subplot(gs[2, 1])
    vars_check = ['er_status', 'pr_status', 'her2_status', 'ki67', 'grade']
    avail = [v for v in vars_check if v in df.columns]
    miss_pct = pd.DataFrame({
        v: df.groupby('cohort')[v].apply(lambda x: x.isna().mean() * 100).reindex(cohort_order)
        for v in avail
    })
    miss_pct.columns = [c.replace('_status', '').replace('_binary', '').upper() for c in miss_pct.columns]
    sns.heatmap(miss_pct, annot=True, fmt='.0f', cmap='YlOrRd', ax=ax, vmin=0, vmax=100,
                cbar_kws={'label': '% Missing', 'shrink': 0.8})
    ax.set_title('F. Missing Data (%)', fontsize=10, fontweight='bold', loc='left')

    plt.savefig(os.path.join(FIG_DIR, 'fig2_cohort.png'), bbox_inches='tight')
    plt.close()


def fig3_forest(results):
    """Forest plot of F1 scores with CIs."""
    print("  Fig 3: Forest plot")

    # Filter to key comparisons
    key_results = [r for r in results if '_f1' in r and r.get('_f1_lo') is not None]
    if not key_results:
        print("    No results with CIs")
        return

    # Organize: for each cohort, show models ordered
    fig, axes = plt.subplots(1, 2, figsize=(7.5, 6), sharey=False)

    for ax_idx, cohort in enumerate(['TCGA-BRCA', 'METABRIC']):
        ax = axes[ax_idx]
        cr = [r for r in key_results if r['Cohort'] == cohort]
        if not cr:
            ax.text(0.5, 0.5, f'No data for {cohort}', transform=ax.transAxes, ha='center')
            continue

        cr.sort(key=lambda r: r['_f1'], reverse=False)

        labels = []
        for i, r in enumerate(cr):
            label = f"{r['Model']} ({r['Feature Set']})"
            color = '#E53935' if 'Surrogate' in r['Model'] else '#1565C0'
            marker = 's' if 'H2H' in r['Model'] else 'o'

            ax.errorbar(r['_f1'], i, xerr=[[r['_f1'] - r['_f1_lo']], [r['_f1_hi'] - r['_f1']]],
                       fmt=marker, color=color, capsize=3, markersize=6, linewidth=1.2)
            labels.append(f"{r['Model']}\n{r['Feature Set']} (n={r['N']})")

        ax.set_yticks(range(len(cr)))
        ax.set_yticklabels(labels, fontsize=7)
        ax.set_xlabel('Macro F1-Score')
        ax.set_title(cohort, fontsize=11, fontweight='bold')
        ax.axvline(x=0.5, color='gray', linestyle=':', alpha=0.5)
        ax.set_xlim(0.2, 0.85)
        ax.grid(True, alpha=0.2, axis='x')

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig3_forest.png'), bbox_inches='tight')
    plt.close()


def fig4_confusion(df, results, le):
    """Key confusion matrices: IHQ surrogate vs best ML, on METABRIC."""
    print("  Fig 4: Confusion matrices")

    # Get METABRIC data with surrogate
    met = df[(df['cohort'] == 'METABRIC') & df['ihq_as_pam50'].isin(PAM50_ORDER)]

    fig, axes = plt.subplots(1, 3, figsize=(7.5, 3))

    # A: IHQ surrogate
    ax = axes[0]
    y_true = le.transform(met['pam50_label'])
    y_surr = le.transform(met['ihq_as_pam50'])
    cm = confusion_matrix(y_true, y_surr, labels=range(4))
    cm_norm = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    sns.heatmap(cm_norm, annot=True, fmt='.2f', cmap='Blues', ax=ax, vmin=0, vmax=1, cbar=False,
                xticklabels=[PAM50_LABELS[s] for s in PAM50_ORDER],
                yticklabels=[PAM50_LABELS[s] for s in PAM50_ORDER])
    ax.set_title('A. IHQ Surrogate\n(METABRIC)', fontsize=9, fontweight='bold')
    ax.set_ylabel('True PAM50')
    ax.set_xlabel('Predicted')
    ax.tick_params(axis='both', labelsize=6)

    # B: XGBoost Set 1 on METABRIC
    met_res = [r for r in results if r['Cohort'] == 'METABRIC' and r['Model'] == 'XGBoost' and r['Feature Set'] == 'Set 1']
    if met_res:
        ax = axes[1]
        r = met_res[0]
        cm2 = confusion_matrix(r['_y_true'], r['_y_pred'], labels=range(4))
        cm2_n = cm2.astype(float) / np.maximum(cm2.sum(axis=1, keepdims=True), 1)
        sns.heatmap(cm2_n, annot=True, fmt='.2f', cmap='Blues', ax=ax, vmin=0, vmax=1, cbar=False,
                    xticklabels=[PAM50_LABELS[s] for s in PAM50_ORDER],
                    yticklabels=[PAM50_LABELS[s] for s in PAM50_ORDER])
        ax.set_title('B. XGBoost Set 1\n(METABRIC)', fontsize=9, fontweight='bold')
        ax.set_xlabel('Predicted')
        ax.tick_params(axis='both', labelsize=6)

    # C: XGBoost Set 2 on METABRIC
    met_res2 = [r for r in results if r['Cohort'] == 'METABRIC' and r['Model'] == 'XGBoost' and r['Feature Set'] == 'Set 2']
    if met_res2:
        ax = axes[2]
        r2 = met_res2[0]
        cm3 = confusion_matrix(r2['_y_true'], r2['_y_pred'], labels=range(4))
        cm3_n = cm3.astype(float) / np.maximum(cm3.sum(axis=1, keepdims=True), 1)
        sns.heatmap(cm3_n, annot=True, fmt='.2f', cmap='Blues', ax=ax, vmin=0, vmax=1, cbar=False,
                    xticklabels=[PAM50_LABELS[s] for s in PAM50_ORDER],
                    yticklabels=[PAM50_LABELS[s] for s in PAM50_ORDER])
        ax.set_title('C. XGBoost Set 2\n(METABRIC)', fontsize=9, fontweight='bold')
        ax.set_xlabel('Predicted')
        ax.tick_params(axis='both', labelsize=6)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig4_confusion.png'), bbox_inches='tight')
    plt.close()


def fig5_greyzone(df, le):
    """Grey zone analysis: confidence vs accuracy."""
    print("  Fig 5: Grey zone")

    train_cohorts = ['GSE81538', 'GSE96058']
    features = ['er_binary', 'pr_binary', 'her2_binary', 'grade']

    train_data = df[df['cohort'].isin(train_cohorts)].dropna(subset=features + ['pam50_label'])
    X_train = train_data[features].values.astype(float)
    y_train = le.transform(train_data['pam50_label'])

    xgb_model = xgb.XGBClassifier(n_estimators=500, max_depth=6, learning_rate=0.1,
                                    objective='multi:softprob', num_class=4,
                                    eval_metric='mlogloss', random_state=42, verbosity=0)
    xgb_model.fit(X_train, y_train)

    met = df[df['cohort'] == 'METABRIC'].dropna(subset=features + ['pam50_label'])
    X_met = met[features].values.astype(float)
    y_met = le.transform(met['pam50_label'])
    probs = xgb_model.predict_proba(X_met)
    y_pred = xgb_model.predict(X_met)
    max_prob = probs.max(axis=1)
    correct = (y_pred == y_met)

    fig, axes = plt.subplots(1, 3, figsize=(7.5, 3))

    # A: Distribution of max probability
    ax = axes[0]
    ax.hist(max_prob[correct], bins=20, alpha=0.6, label='Correct', color='#4CAF50', density=True)
    ax.hist(max_prob[~correct], bins=20, alpha=0.6, label='Incorrect', color='#E53935', density=True)
    ax.set_xlabel('Maximum Predicted Probability')
    ax.set_ylabel('Density')
    ax.set_title('A. Prediction Confidence', fontsize=9, fontweight='bold')
    ax.legend(fontsize=7)

    # B: Accuracy by confidence bin
    ax = axes[1]
    bins = np.arange(0.25, 1.01, 0.05)
    bin_idx = np.digitize(max_prob, bins)
    bin_acc = []
    bin_centers = []
    bin_ns = []
    for i in range(1, len(bins)):
        mask = bin_idx == i
        if mask.sum() > 5:
            bin_acc.append(correct[mask].mean())
            bin_centers.append((bins[i-1] + bins[i]) / 2)
            bin_ns.append(mask.sum())

    ax.bar(bin_centers, bin_acc, width=0.04, color='#1565C0', alpha=0.7)
    ax.axhline(y=correct.mean(), color='red', linestyle='--', alpha=0.5, linewidth=0.8)
    ax.text(0.35, correct.mean() + 0.03, f'Overall: {correct.mean():.1%}', color='red', fontsize=7)
    ax.set_xlabel('Maximum Predicted Probability')
    ax.set_ylabel('Accuracy')
    ax.set_title('B. Accuracy by Confidence', fontsize=9, fontweight='bold')
    ax.set_ylim(0, 1)

    # C: PAM50 subtype composition by confidence zone
    ax = axes[2]
    zones = {'Low (<0.50)': max_prob < 0.5, 'Medium': (max_prob >= 0.5) & (max_prob < 0.7), 'High (>0.70)': max_prob >= 0.7}
    zone_data = []
    for zname, zmask in zones.items():
        if zmask.sum() == 0:
            continue
        for sub_idx, sub in enumerate(PAM50_ORDER):
            zone_data.append({
                'Zone': zname, 'Subtype': PAM50_LABELS[sub],
                'Proportion': (y_met[zmask] == sub_idx).mean()
            })
    zdf = pd.DataFrame(zone_data)
    zpivot = zdf.pivot(index='Zone', columns='Subtype', values='Proportion').fillna(0)
    zpivot = zpivot.reindex(columns=[PAM50_LABELS[s] for s in PAM50_ORDER])
    zpivot.plot(kind='bar', stacked=True, ax=ax,
                color=[PAM50_COLORS[s] for s in PAM50_ORDER], width=0.6)
    ax.set_ylabel('Proportion')
    ax.set_title('C. Subtype by Confidence', fontsize=9, fontweight='bold')
    ax.legend(fontsize=6, loc='upper right')
    ax.tick_params(axis='x', rotation=0)
    ax.set_xlabel('')
    ax.set_ylim(0, 1)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig5_greyzone.png'), bbox_inches='tight')
    plt.close()


def fig6_importance(df, le):
    """Feature importance with per-class breakdown."""
    print("  Fig 6: Feature importance")

    train_cohorts = ['GSE81538', 'GSE96058']
    features = ['er_binary', 'pr_binary', 'her2_binary', 'ki67', 'grade']
    available = [f for f in features if f in df.columns]

    train_data = df[df['cohort'].isin(train_cohorts)].dropna(subset=available + ['pam50_label'])
    if len(train_data) < 50:
        return

    X = train_data[available].values.astype(float)
    y = le.transform(train_data['pam50_label'])

    model = xgb.XGBClassifier(n_estimators=500, max_depth=6, learning_rate=0.1,
                                objective='multi:softprob', num_class=4,
                                eval_metric='mlogloss', random_state=42, verbosity=0)
    model.fit(X, y)

    imp = model.feature_importances_
    sorted_idx = np.argsort(imp)[::-1]

    fig, ax = plt.subplots(figsize=(4, 3))
    names = [available[i].replace('_binary', '').upper() for i in sorted_idx]
    colors_bar = ['#1565C0' if imp[i] == imp.max() else '#64B5F6' for i in sorted_idx]
    ax.barh(range(len(imp)), imp[sorted_idx], color=colors_bar, height=0.6)
    ax.set_yticks(range(len(imp)))
    ax.set_yticklabels(names)
    ax.set_xlabel('Feature Importance (Gain)')
    ax.set_title('Feature Importance (XGBoost)', fontsize=10, fontweight='bold')
    ax.invert_yaxis()

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, 'fig6_importance.png'), bbox_inches='tight')
    plt.close()


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    df, results, le = run_full_analysis()
    generate_pub_figures(df, results, le)

    print("\n=== DONE ===")
    print(f"Tables: {os.listdir(TAB_DIR)}")
    print(f"Figures: {os.listdir(FIG_DIR)}")
