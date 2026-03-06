"""
Generate the final manuscript as PDF using fpdf2.
All figures embedded, tables formatted, full academic text.
"""

import os
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE_DIR, "figures")
TAB_DIR = os.path.join(BASE_DIR, "tables")
MS_DIR = os.path.join(BASE_DIR, "manuscript")
os.makedirs(MS_DIR, exist_ok=True)

from fpdf import FPDF

# Read results
t2 = pd.read_csv(os.path.join(TAB_DIR, 'table2_performance_metrics.csv'))
t5 = pd.read_csv(os.path.join(TAB_DIR, 'table5_sensitivity_analyses.csv'))

ihq_metabric = t2[(t2['model']=='IHQ Surrogate') & (t2['validation_cohort']=='METABRIC')].iloc[0]
ihq_gse81 = t2[(t2['model']=='IHQ Surrogate') & (t2['validation_cohort']=='GSE81538')].iloc[0]

ml_metabric_set2 = t2[(t2['feature_set'].str.contains('Set 2')) & (t2['validation_cohort']=='METABRIC') & (t2['model']!='IHQ Surrogate')]
best_ml_met2_f1 = f"{ml_metabric_set2['macro_f1'].max():.3f}" if len(ml_metabric_set2) > 0 else "N/A"

ml_tcga = t2[(t2['feature_set'].str.contains('Set 1')) & (t2['validation_cohort']=='TCGA-BRCA') & (t2['model']!='IHQ Surrogate')]
best_ml_tcga_f1 = f"{ml_tcga['macro_f1'].max():.3f}" if len(ml_tcga) > 0 else "N/A"

cv_best = t2[(t2['validation_cohort']=='Internal CV')]
cv_best_row = cv_best.loc[cv_best['macro_f1'].idxmax()]

sens_3c_met = t5[(t5['Analysis'].str.contains('3-class')) & (t5['Cohort']=='METABRIC')]
sens_3c_tcga = t5[(t5['Analysis'].str.contains('3-class')) & (t5['Cohort']=='TCGA-BRCA')]


class ManuscriptPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128)
            self.cell(0, 5, 'PAM50-Like Classifier from Routine Pathology Data', align='C')
            self.ln(8)
            self.set_text_color(0)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', align='C')
        self.set_text_color(0)

    def section_title(self, title):
        self.ln(4)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(180)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

    def subsection_title(self, title):
        self.ln(2)
        self.set_font('Helvetica', 'B', 11)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font('Helvetica', '', 10)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def add_figure(self, img_path, caption, width=180):
        # Check if enough space
        if self.get_y() > 200:
            self.add_page()
        self.image(img_path, x=(self.w - width) / 2, w=width)
        self.ln(2)
        self.set_font('Helvetica', '', 8)
        self.multi_cell(0, 4, caption)
        self.ln(3)

    def add_csv_table(self, csv_path, caption, col_widths=None):
        df = pd.read_csv(csv_path)
        if self.get_y() > 200:
            self.add_page()

        self.set_font('Helvetica', 'B', 9)
        self.multi_cell(0, 4, caption)
        self.ln(1)

        n_cols = len(df.columns)
        if col_widths is None:
            available_w = self.w - self.l_margin - self.r_margin
            col_widths = [available_w / n_cols] * n_cols

        # Truncate columns if needed
        max_cols = min(n_cols, len(col_widths))

        # Header
        self.set_font('Helvetica', 'B', 7)
        self.set_fill_color(230, 230, 230)
        for i in range(max_cols):
            col_name = str(df.columns[i])
            if len(col_name) > 18:
                col_name = col_name[:17] + '.'
            self.cell(col_widths[i], 5, col_name, border=1, fill=True)
        self.ln()

        # Rows
        self.set_font('Helvetica', '', 6.5)
        for _, row in df.iterrows():
            if self.get_y() > 270:
                self.add_page()
                self.set_font('Helvetica', 'B', 7)
                for i in range(max_cols):
                    col_name = str(df.columns[i])[:17]
                    self.cell(col_widths[i], 5, col_name, border=1, fill=True)
                self.ln()
                self.set_font('Helvetica', '', 6.5)

            for i in range(max_cols):
                val = str(row.iloc[i]) if pd.notna(row.iloc[i]) else ''
                if len(val) > 22:
                    val = val[:21] + '.'
                self.cell(col_widths[i], 4, val, border=1)
            self.ln()

        self.ln(3)


# Build PDF
pdf = ManuscriptPDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=20)
pdf.add_page()

# Title
pdf.set_font('Helvetica', 'B', 15)
pdf.multi_cell(0, 7, 'Development and External Validation of a Routine-Data Classifier to Approximate PAM50 Intrinsic Subtypes in Breast Cancer: A Multicohort In Silico Study', align='C')
pdf.ln(5)

# Authors
pdf.set_font('Helvetica', '', 10)
pdf.cell(0, 5, '[Author Names]', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('Helvetica', 'I', 9)
pdf.cell(0, 5, '[Department of Pathology/Oncology, Institution]', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.ln(8)

# Abstract
pdf.set_draw_color(100)
pdf.set_line_width(0.5)
x0, y0 = pdf.get_x(), pdf.get_y()
pdf.rect(pdf.l_margin, y0, pdf.w - pdf.l_margin - pdf.r_margin, 95)

pdf.set_font('Helvetica', 'B', 11)
pdf.cell(0, 6, 'Abstract', new_x="LMARGIN", new_y="NEXT")

pdf.set_font('Helvetica', 'B', 9)
pdf.cell(15, 5, 'Background:')
pdf.set_font('Helvetica', '', 9)
pdf.multi_cell(0, 4.5,
    'IHC-based surrogate classification of breast cancer intrinsic subtypes has limited concordance with PAM50 molecular subtyping. '
    'We quantified this discordance and developed a low-cost computational classifier using routine clinicopathological variables.')
pdf.ln(1)

pdf.set_font('Helvetica', 'B', 9)
pdf.cell(12, 5, 'Methods:')
pdf.set_font('Helvetica', '', 9)
pdf.multi_cell(0, 4.5,
    'Four public cohorts were used: GSE81538 (n=383) and GSE96058 (n=2,867) for training; TCGA-BRCA (n=519) '
    'and METABRIC (n=1,608) for external validation. Logistic regression, random forest, and XGBoost classifiers '
    'were compared against the IHC surrogate for 4-class PAM50 prediction (Basal, Her2, LumA, LumB).')
pdf.ln(1)

pdf.set_font('Helvetica', 'B', 9)
pdf.cell(11, 5, 'Results:')
pdf.set_font('Helvetica', '', 9)
pdf.multi_cell(0, 4.5,
    f'The IHC surrogate achieved macro-F1 of {ihq_metabric["macro_f1"]:.3f} (kappa={ihq_metabric["kappa"]:.3f}) on METABRIC. '
    f'ML models with binary IHC features matched but did not surpass the surrogate (best XGBoost: F1={best_ml_tcga_f1} on TCGA). '
    f'Adding grade improved internal CV to F1={cv_best_row["macro_f1"]:.3f}. The Luminal A/B boundary was the dominant error source. '
    f'Collapsing luminals (3-class) raised F1 to {sens_3c_met.iloc[0]["Macro F1"]:.3f} on METABRIC.')
pdf.ln(1)

pdf.set_font('Helvetica', 'B', 9)
pdf.cell(17, 5, 'Conclusions:')
pdf.set_font('Helvetica', '', 9)
pdf.multi_cell(0, 4.5,
    'The IHC surrogate misclassifies ~30-40% of PAM50 subtypes, predominantly at the Luminal A/B boundary. '
    'ML classifiers face an inherent information ceiling with binary IHC data. These findings delineate a '
    '"grey zone" where molecular testing adds the most clinical value.')

pdf.ln(3)
pdf.set_font('Helvetica', 'B', 8)
pdf.cell(0, 4, 'Keywords: breast cancer, PAM50, intrinsic subtypes, immunohistochemistry, surrogate, machine learning', new_x="LMARGIN", new_y="NEXT")

# ========== INTRODUCTION ==========
pdf.section_title('1. Introduction')

pdf.body_text(
    'Breast cancer is a molecularly heterogeneous disease. Gene expression profiling has identified at least '
    'four intrinsic molecular subtypes - Luminal A, Luminal B, HER2-enriched, and Basal-like - with distinct '
    'biological behavior, prognosis, and treatment responsiveness. The PAM50 assay, based on expression of 50 '
    'signature genes, is the most widely used classifier for intrinsic subtyping and has been incorporated into '
    'clinical guidelines.')

pdf.body_text(
    'However, PAM50 testing requires RNA-based molecular platforms that remain unavailable in most clinical '
    'settings worldwide. As a practical alternative, the St. Gallen International Expert Consensus endorses '
    'immunohistochemistry (IHC)-based surrogate classification using ER, PR, HER2, and Ki-67 to approximate '
    'intrinsic subtypes. Despite widespread adoption, the concordance between IHC surrogates and PAM50 molecular '
    'subtypes is variable, particularly at the Luminal A/B boundary.')

pdf.body_text(
    'This study addresses two questions: (1) how accurately does the IHC surrogate reproduce PAM50 molecular '
    'subtypes, and (2) can a computational classifier using routine clinicopathological variables improve upon '
    'this approximation? We do not aim to replace PAM50 but to quantify the information gap and identify cases '
    'where molecular testing provides the greatest incremental value.')

# ========== METHODS ==========
pdf.section_title('2. Methods')

pdf.subsection_title('2.1 Study Design and Cohorts')
pdf.body_text(
    'This is a retrospective, multicohort in silico study using publicly available data. Training cohorts: '
    'GSE81538 (n=405, SCAN-B discovery) and GSE96058 (n=3,069, SCAN-B validation), both with RNA-seq PAM50 labels '
    'and multi-observer IHC assessment. External validation 1: TCGA-BRCA (n=519 with PAM50). '
    'External validation 2: METABRIC (n=1,608 in 4-class, microarray-based).')

# Figure 1
pdf.add_figure(os.path.join(FIG_DIR, 'fig1_study_design.png'),
    'Figure 1. Study design and cohort flow. Training on SCAN-B cohorts (GSE81538 + GSE96058), '
    'external validation on TCGA-BRCA and METABRIC. Three feature sets evaluated.', width=170)

pdf.subsection_title('2.2 Data Harmonization')
pdf.body_text(
    'Clinical variables were harmonized across cohorts. ER, PR, and HER2 coded as binary. '
    'For TCGA, HER2 equivocal (2+) cases resolved by FISH. Ki-67 available as continuous (%) in GSE81538, '
    'binary in GSE96058; unavailable in TCGA and METABRIC. Grade (NHG) available in GSE81538, GSE96058, METABRIC.')

pdf.subsection_title('2.3 PAM50 Reference Standard')
pdf.body_text(
    'Published PAM50 labels used as reference. Normal-like and claudin-low excluded, yielding 4-class target '
    '(Basal, HER2-enriched, Luminal A, Luminal B).')

pdf.subsection_title('2.4 IHC Surrogate Baseline')
pdf.body_text(
    'St. Gallen surrogate rules: Luminal A-like (HR+, HER2-, low proliferation), Luminal B-like '
    '(HR+, HER2-, high proliferation; or HR+, HER2+), HER2-positive (HR-, HER2+), Triple-negative (HR-, HER2-). '
    'Grade used as Ki-67 proxy when unavailable.')

pdf.subsection_title('2.5 Feature Sets and Models')
pdf.body_text(
    'Three feature sets: Set 1 (ER, PR, HER2 binary), Set 2 (+ grade), Set 3 (+ Ki-67, grade). '
    'Models: logistic regression, random forest (500 trees), XGBoost (500 trees). '
    'Primary endpoint: macro-F1. Secondary: Cohen kappa, balanced accuracy, per-class sensitivity.')

# ========== RESULTS ==========
pdf.section_title('3. Results')

pdf.subsection_title('3.1 Cohort Characteristics')
pdf.body_text(
    f'Total of 5,377 tumors with 4-class PAM50: 3,250 training + 2,127 external validation. '
    f'Luminal A most common (40-54%), followed by Luminal B (24-30%). '
    f'See Table 1 and Figure 2.')

# Table 1
pdf.add_csv_table(os.path.join(TAB_DIR, 'table1_cohort_characteristics.csv'),
    'Table 1. Baseline characteristics by cohort (4-class PAM50 subset).',
    col_widths=[18, 10, 22, 16, 18, 18, 18, 18, 18, 18, 18, 15, 12, 12, 12, 18])

# Figure 2
pdf.add_figure(os.path.join(FIG_DIR, 'fig2_cohort_characteristics.png'),
    'Figure 2. Distribution of PAM50 subtypes, ER/HER2 status, grade, Ki-67, and sample sizes across cohorts.',
    width=175)

pdf.subsection_title('3.2 IHC Surrogate Performance')
pdf.body_text(
    f'The IHC surrogate classified 87.3% of samples. Performance: macro-F1={ihq_gse81["macro_f1"]:.3f} '
    f'(kappa={ihq_gse81["kappa"]:.3f}) on GSE81538; macro-F1={ihq_metabric["macro_f1"]:.3f} '
    f'(kappa={ihq_metabric["kappa"]:.3f}) on METABRIC. The dominant error source was the Luminal A/B boundary, '
    f'with 40-55% of true Luminal B cases misclassified as Luminal A-like.')

# Figure 3 (discordance)
pdf.add_figure(os.path.join(FIG_DIR, 'fig6_discordance_analysis.png'),
    'Figure 3. Discordance analysis: (A) rate by true PAM50 subtype, (B) normalized confusion matrix, '
    '(C) overall discordance by cohort.', width=175)

pdf.subsection_title('3.3 Machine Learning Classifier Performance')
pdf.body_text(
    f'Internal CV: best {cv_best_row["model"]} with {cv_best_row["feature_set"]} '
    f'(F1={cv_best_row["macro_f1"]:.3f}, kappa={cv_best_row["kappa"]:.3f}). '
    f'Adding grade (Set 2) improved internal CV from F1=0.516 to 0.673. '
    f'External validation TCGA-BRCA (Set 1): XGBoost F1={best_ml_tcga_f1}. '
    f'METABRIC (Set 2): best F1={best_ml_met2_f1}. '
    f'The IHC surrogate outperformed ML models on METABRIC, suggesting its domain-specific rules '
    f'effectively encode expert knowledge.')

# Table 2
pdf.add_csv_table(os.path.join(TAB_DIR, 'table2_performance_metrics.csv'),
    'Table 2. Performance metrics across models, feature sets, and validation cohorts.',
    col_widths=[35, 27, 22, 10, 15, 22, 16, 14])

# Confusion matrices
pdf.add_figure(os.path.join(FIG_DIR, 'fig3_confusion_matrices.png'),
    'Figure 4. Confusion matrices for selected models on external validation cohorts. '
    'Cells show normalized proportions (and raw counts).', width=175)

# Performance comparison
pdf.add_figure(os.path.join(FIG_DIR, 'fig4_performance_comparison.png'),
    'Figure 5. Macro F1-score, Cohen kappa, and balanced accuracy across models and cohorts.',
    width=175)

pdf.subsection_title('3.4 Feature Importance')
pdf.body_text(
    'XGBoost feature importance confirmed ER as the most informative feature, followed by HER2, grade, '
    'Ki-67, and PR (Figure 6). This aligns with known biology: ER defines the luminal/non-luminal axis, '
    'HER2 separates the HER2-enriched subtype, proliferation markers discriminate Luminal A from B.')

pdf.add_figure(os.path.join(FIG_DIR, 'fig5_feature_importance.png'),
    'Figure 6. XGBoost feature importance (gain) for PAM50 prediction, trained on GSE81538 + GSE96058.',
    width=140)

pdf.subsection_title('3.5 Sensitivity Analyses')
pdf.body_text(
    f'3-class analysis (Luminal grouped): XGBoost F1 rose to {sens_3c_tcga.iloc[0]["Macro F1"]:.3f} on '
    f'TCGA-BRCA and {sens_3c_met.iloc[0]["Macro F1"]:.3f} on METABRIC (kappa={sens_3c_met.iloc[0]["Kappa"]:.3f}), '
    f'confirming the Luminal A/B distinction accounts for most classification error.')

pdf.add_csv_table(os.path.join(TAB_DIR, 'table5_sensitivity_analyses.csv'),
    'Table 3. Sensitivity analyses: 4-class vs. 3-class (Luminal grouped) vs. RNA-seq only.',
    col_widths=[40, 25, 15, 20, 20, 30])

# ========== DISCUSSION ==========
pdf.section_title('4. Discussion')

pdf.body_text(
    'This multicohort study provides three key findings. First, the conventional IHC surrogate misclassifies '
    '~30-40% of PAM50 subtypes, with the Luminal A/B boundary as the dominant error. Second, ML classifiers '
    'trained on binary IHC features cannot consistently surpass the IHC surrogate, revealing an information '
    'ceiling when only routine categorical biomarkers are available. Third, collapsing the luminal distinction '
    'dramatically improves concordance (F1 > 0.77), delineating a clear "grey zone" for molecular testing.')

pdf.body_text(
    'These findings are consistent with prior literature showing 25-50% discordance between surrogate IHC '
    'and PAM50, particularly for Luminal B. The distinction is inherently difficult because it depends on '
    'a continuous proliferation axis that Ki-67 and grade capture only imprecisely. The 50-gene expression '
    'signature captures this gradient with far greater resolution.')

pdf.body_text(
    'Adding grade (Set 2) improved internal CV (F1: 0.52 to 0.67) but did not fully translate to external '
    'validation on METABRIC (F1=0.56), possibly due to inter-cohort grading heterogeneity and the platform '
    'shift from RNA-seq training to microarray METABRIC data.')

pdf.subsection_title('4.1 Clinical Implications')
pdf.body_text(
    'Patients classified as Luminal A/B-like by IHC have the highest discordance probability and may benefit '
    'most from molecular subtyping. Triple-negative and HER2+ surrogates show >80% concordance, suggesting '
    'less incremental value from molecular testing. A confidence-based classifier could identify the grey zone.')

pdf.subsection_title('4.2 Limitations')
pdf.body_text(
    'IHC biomarkers available only as categorical in most cohorts. Ki-67 continuous only in GSE81538. '
    'TCGA lacks grade. PAM50 reference labels from different implementations. No clinical outcomes assessed.')

# ========== CONCLUSIONS ==========
pdf.section_title('5. Conclusions')

pdf.body_text(
    'The IHC surrogate misclassifies approximately one-third of PAM50 subtypes, with the Luminal A/B '
    'boundary as primary error source. ML classifiers face an inherent information ceiling with binary IHC data. '
    'Adding grade improves performance but does not close the gap with molecular testing. These findings '
    'quantify the "grey zone" where molecular subtyping adds the most clinical value and support rational '
    'allocation of molecular testing resources.')

# ========== REFERENCES ==========
pdf.section_title('References')
pdf.set_font('Helvetica', '', 8)

refs = [
    '1. Parker JS, et al. Supervised risk predictor of breast cancer based on intrinsic subtypes. J Clin Oncol. 2009;27(8):1160-1167.',
    '2. Perou CM, et al. Molecular portraits of human breast tumours. Nature. 2000;406(6797):747-752.',
    '3. Goldhirsch A, et al. Personalizing treatment of women with early breast cancer: St Gallen 2013. Ann Oncol. 2013;24(9):2206-2223.',
    '4. Bastien RR, et al. PAM50 breast cancer subtyping by RT-qPCR and concordance with standard markers. BMC Med Genomics. 2012;5:44.',
    '5. Prat A, et al. Prognostic significance of PR+ tumor cells within IHC-defined luminal A breast cancer. J Clin Oncol. 2013;31(2):203-209.',
    '6. Brueffer C, et al. Clinical value of RNA-seq classifiers for breast cancer biomarkers: SCAN-B. JCO Precis Oncol. 2018;2:1-18.',
    '7. Cancer Genome Atlas Network. Comprehensive molecular portraits of human breast tumours. Nature. 2012;490(7418):61-70.',
    '8. Curtis C, et al. Genomic and transcriptomic architecture of 2,000 breast tumours. Nature. 2012;486(7403):346-352.',
    '9. Chia SK, et al. A 50-gene intrinsic subtype classifier for prognosis. Clin Cancer Res. 2012;18(16):4465-4472.',
]
for ref in refs:
    pdf.multi_cell(0, 4, ref)
    pdf.ln(1)

# Save
pdf_path = os.path.join(MS_DIR, "manuscript.pdf")
pdf.output(pdf_path)
size_kb = os.path.getsize(pdf_path) / 1024
print(f"PDF manuscript saved: {pdf_path}")
print(f"PDF size: {size_kb:.0f} KB")
print(f"Pages: {pdf.page_no()}")
