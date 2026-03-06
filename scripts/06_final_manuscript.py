"""
Final manuscript PDF -- user's suggested text version.
Uses fpdf2, Helvetica only (ASCII safe).
Embeds all 6 publication figures from 05_enhanced_analysis.
"""

import os, sys
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE_DIR, "figures")
TAB_DIR = os.path.join(BASE_DIR, "tables")
MS_DIR = os.path.join(BASE_DIR, "manuscript")
os.makedirs(MS_DIR, exist_ok=True)

# Load result tables
t_main = pd.read_csv(os.path.join(TAB_DIR, 'table_main_results.csv'))
t_flow = pd.read_csv(os.path.join(TAB_DIR, 'table_sample_flow.csv'))
t_lumab = pd.read_csv(os.path.join(TAB_DIR, 'table_lumAB_crossover.csv'))
t_gz = pd.read_csv(os.path.join(TAB_DIR, 'table_grey_zone.csv'))
t_sens = pd.read_csv(os.path.join(TAB_DIR, 'table_sensitivity_enhanced.csv'))
t1 = pd.read_csv(os.path.join(TAB_DIR, 'table1_cohort_characteristics.csv'))


class ManuscriptPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 7)
            self.set_text_color(120)
            self.cell(0, 4,
                'Routine Pathology Data Cannot Reliably Reproduce PAM50 Intrinsic Subtypes',
                align='C')
            self.ln(6)
            self.set_text_color(0)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(120)
        self.cell(0, 10, f'{self.page_no()}', align='C')
        self.set_text_color(0)

    def h1(self, text):
        self.ln(3)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0)
        self.set_line_width(0.4)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(2)

    def h2(self, text):
        self.ln(2)
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def p(self, text):
        self.set_font('Helvetica', '', 9)
        self.multi_cell(0, 4.5, text)
        self.ln(1)

    def p_bold_start(self, bold_text, normal_text):
        self.set_font('Helvetica', 'B', 9)
        w_bold = self.get_string_width(bold_text) + 1
        self.cell(w_bold, 4.5, bold_text)
        self.set_font('Helvetica', '', 9)
        self.multi_cell(0, 4.5, normal_text)
        self.ln(0.5)

    def fig(self, path, caption, w=170):
        if self.get_y() > 200:
            self.add_page()
        self.image(path, x=(self.w - w) / 2, w=w)
        self.ln(2)
        self.set_font('Helvetica', 'I', 7.5)
        self.multi_cell(0, 3.5, caption)
        self.ln(3)

    def small_table(self, df, caption, max_cols=None):
        if self.get_y() > 220:
            self.add_page()
        self.set_font('Helvetica', 'B', 8)
        self.multi_cell(0, 4, caption)
        self.ln(1)

        cols = list(df.columns)
        if max_cols:
            cols = cols[:max_cols]
        n = len(cols)
        w = (self.w - self.l_margin - self.r_margin) / n

        self.set_font('Helvetica', 'B', 6.5)
        self.set_fill_color(235, 235, 235)
        for c in cols:
            self.cell(w, 4, str(c)[:22], border=1, fill=True)
        self.ln()

        self.set_font('Helvetica', '', 6)
        for _, row in df.iterrows():
            if self.get_y() > 270:
                self.add_page()
            for c in cols:
                val = str(row[c]) if pd.notna(row[c]) else ''
                self.cell(w, 3.5, val[:26], border=1)
            self.ln()
        self.ln(2)


# ============================================================
# BUILD PDF
# ============================================================
pdf = ManuscriptPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# ---- TITLE ----
pdf.set_font('Helvetica', 'B', 14)
pdf.multi_cell(0, 6.5,
    'Routine Pathology Data Cannot Reliably Reproduce\n'
    '4-Class PAM50 Intrinsic Subtypes in Breast Cancer:\n'
    'A Multicohort In Silico Study', align='C')
pdf.ln(4)

pdf.set_font('Helvetica', '', 9)
pdf.cell(0, 4, '[Author Names]', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.set_font('Helvetica', 'I', 8)
pdf.cell(0, 4, '[Institutional Affiliations]', align='C', new_x="LMARGIN", new_y="NEXT")
pdf.ln(6)

# ---- ABSTRACT ----
pdf.set_draw_color(80)
pdf.set_line_width(0.3)
y0 = pdf.get_y()
# We'll draw the box after writing content; use a fixed height estimate
pdf.set_font('Helvetica', 'B', 10)
pdf.cell(0, 5, 'ABSTRACT', new_x="LMARGIN", new_y="NEXT")
pdf.ln(1)

pdf.p_bold_start('Background: ',
    'Immunohistochemistry (IHC)-based surrogate classification is widely used to approximate '
    'PAM50 intrinsic breast cancer subtypes when gene-expression profiling is unavailable. '
    'Whether machine-learning (ML) algorithms applied to the same routine variables can improve '
    'upon the surrogate has not been rigorously tested across independent cohorts.')

pdf.p_bold_start('Methods: ',
    'We harmonised four public datasets (GSE81538, n = 383; GSE96058, n = 2,867; TCGA-BRCA, '
    'n = 519; METABRIC, n = 1,608; total 5,377 tumours with 4-class PAM50 labels). Three ML '
    'classifiers (logistic regression, random forest, XGBoost) were trained on the SCAN-B '
    'cohorts using feature sets of increasing complexity (Set 1: ER/PR/HER2; Set 2: + grade; '
    'Set 3: + Ki-67) and evaluated on two external cohorts. Head-to-head comparisons against '
    'the IHC surrogate were performed on identical sample subsets; all metrics carry bootstrap '
    '95 % confidence intervals (1,000 resamples).')

pdf.p_bold_start('Results: ',
    'On METABRIC (head-to-head, n = 1,554), the IHC surrogate achieved macro-F1 = 0.646 '
    '(95 % CI 0.623-0.669) versus best ML 0.559 (0.533-0.584; XGBoost, Set 2). The Luminal '
    'A/B boundary was the dominant error source: 42.5 % of true Luminal B cases received a '
    'Luminal A-like surrogate label; collapsing both luminal classes into one raised macro-F1 '
    'to 0.767. A grey-zone analysis showed that 13.5 % of cases (max predicted probability '
    '< 0.50) were 73.6 % luminal and had only 15.9 % ML accuracy.')

pdf.p_bold_start('Conclusions: ',
    'Routine clinicopathological variables contain insufficient information to reproduce '
    '4-class PAM50 subtypes reliably. The irreducible uncertainty concentrates at the Luminal '
    'A/B boundary, defining a clinically actionable grey zone where molecular testing adds the '
    'greatest value.')

pdf.ln(1)
pdf.set_font('Helvetica', 'B', 7.5)
pdf.cell(0, 4,
    'Keywords: breast cancer, PAM50, intrinsic subtypes, immunohistochemistry, '
    'machine learning, information ceiling',
    new_x="LMARGIN", new_y="NEXT")

# ============================================================
# 1. INTRODUCTION
# ============================================================
pdf.h1('1. Introduction')

pdf.p(
    'Breast cancer is a molecularly heterogeneous disease. Gene-expression profiling '
    'identifies at least four intrinsic subtypes -- Luminal A, Luminal B, HER2-enriched, and '
    'Basal-like -- each carrying distinct prognostic trajectories and treatment implications '
    '[1,2]. The PAM50 assay, based on a 50-gene expression signature, is the reference standard '
    'for intrinsic subtype assignment and informs clinical decisions on adjuvant therapy '
    'escalation or de-escalation [3].')

pdf.p(
    'Because gene-expression testing requires fresh/frozen tissue, specialised platforms, and '
    'significant cost, most centres worldwide rely on immunohistochemistry (IHC) surrogates '
    'endorsed by the St. Gallen consensus [4]. These surrogates map combinations of ER, PR, '
    'HER2, and Ki-67 (or histological grade) to "Luminal A-like", "Luminal B-like", '
    '"HER2-positive", and "Triple-negative" categories intended to mirror intrinsic subtypes. '
    'Published concordance between IHC surrogates and PAM50 ranges from 50 % to 80 %, with '
    'well-documented weakness at the Luminal A/B boundary [5,6].')

pdf.p(
    'An intuitive next step is to ask whether machine-learning (ML) algorithms, trained on the '
    'same routine variables, can extract additional discriminative signal and outperform the '
    'rule-based surrogate. If so, a simple software upgrade could improve subtype assignment at '
    'no additional laboratory cost. If not, the negative result is equally informative: it '
    'implies that routine data contain an information ceiling that no algorithm can overcome, '
    'and that molecular testing is irreplaceable for specific patient subgroups.')

pdf.p(
    'This study tests the latter hypothesis in a multicohort in silico framework. We train '
    'three ML classifiers on two SCAN-B cohorts (n = 3,250), evaluate them on TCGA-BRCA '
    '(n = 519) and METABRIC (n = 1,608), and compare every model head-to-head with the IHC '
    'surrogate on identical sample subsets. We further introduce a grey-zone analysis that '
    'stratifies cases by prediction confidence to identify the patient population most likely '
    'to benefit from molecular subtyping.')

# ============================================================
# 2. METHODS
# ============================================================
pdf.h1('2. Methods')

pdf.h2('2.1 Study Design')
pdf.p(
    'Retrospective, purely in silico, multicohort diagnostic-accuracy study. The index test is '
    'each ML classifier (or the IHC surrogate); the reference standard is the published PAM50 '
    'label in each cohort. No new biological samples were analysed.')

pdf.h2('2.2 Data Sources and Cohorts')
pdf.p(
    'Four publicly available breast cancer datasets were used (Table 1, Figure 1):')

pdf.p(
    'Training set -- (1) GSE81538 (SCAN-B, n = 405; 383 with 4-class PAM50): RNA-seq with '
    'multi-observer IHC consensus for ER, PR, HER2, Ki-67, and NHG grade [7]. '
    '(2) GSE96058 (SCAN-B, n = 3,069; 2,867 with 4-class PAM50): RNA-seq; binary IHC status '
    'and NHG grade available [7].')

pdf.p(
    'External validation -- (3) TCGA-BRCA (n = 1,108 clinical; 519 with published PAM50 from '
    'brca_tcga_pub): RNA-seq; ER, PR, HER2 from IHC/FISH, no grade [8]. '
    '(4) METABRIC (n = 2,509 clinical; 1,608 with 4-class PAM50): Illumina microarray; '
    'ER, PR, HER2, NHG grade available, no Ki-67 [9].')

pdf.p(
    'Normal-like and claudin-low subtypes were excluded to yield a standard 4-class target. '
    'All data were downloaded from NCBI GEO (series matrix files) or cBioPortal (REST API).')

# Figure 1 -- study flow
pdf.fig(os.path.join(FIG_DIR, 'fig1_flow.png'),
    'Figure 1. Study design and sample flow. Two SCAN-B cohorts form the training set; '
    'TCGA-BRCA and METABRIC serve as external validation. Three feature sets of increasing '
    'complexity are evaluated against the IHC surrogate baseline on identical sample subsets.',
    w=155)

# Table 1 -- sample flow
pdf.small_table(t_flow,
    'Table 1. Sample flow and feature-set availability by cohort.')

pdf.h2('2.3 Variable Harmonisation')
pdf.p(
    'ER and PR were coded as binary positive/negative across all cohorts. HER2 was binary; '
    'equivocal IHC results were resolved by FISH when available (TCGA). Ki-67 was available '
    'as a continuous percentage only in GSE81538; in GSE96058 it was stored as a binary '
    'high/low flag (mapped to proxy values of 30 % and 10 %, respectively). Ki-67 was absent '
    'in TCGA and METABRIC. Histological grade (NHG, 1-3) was present in GSE81538, GSE96058, '
    'and METABRIC but absent in TCGA-BRCA.')

pdf.h2('2.4 IHC Surrogate Classification')
pdf.p(
    'The conventional surrogate followed St. Gallen 2013 rules [4]: '
    'Luminal A-like = HR+/HER2-/low proliferation; '
    'Luminal B-like = HR+/HER2-/high proliferation, or HR+/HER2+; '
    'HER2-positive (non-luminal) = HR-/HER2+; '
    'Triple-negative = HR-/HER2-. '
    'Proliferation was defined as Ki-67 >= 20 % when available, or grade 3 as proxy. '
    'Cases missing ER, PR, or HER2 were excluded from surrogate classification.')

pdf.h2('2.5 Feature Sets')
pdf.p(
    'Three nested sets reflected real-world data availability: '
    'Set 1 (Core IHC): ER, PR, HER2 -- universally available. '
    'Set 2 (IHC + Grade): adds histological grade (available in GSE81538, GSE96058, METABRIC). '
    'Set 3 (IHC + Ki-67 + Grade): adds continuous Ki-67 (available only in GSE81538 + partial '
    'GSE96058). Set 3 was evaluable only on the training cohorts and is not reported for '
    'external validation.')

pdf.h2('2.6 Machine-Learning Models')
pdf.p(
    'Three classifiers were trained on the combined GSE81538 + GSE96058 training set: '
    '(i) multinomial logistic regression with balanced class weights; '
    '(ii) random forest (500 trees, balanced class weights); '
    '(iii) XGBoost (500 rounds, max depth 6, learning rate 0.1). '
    'No hyperparameter tuning was performed on the validation cohorts.')

pdf.h2('2.7 Statistical Analysis')
pdf.p(
    'Primary endpoint: macro-averaged F1-score. Secondary endpoints: Cohen\'s kappa (linear '
    'weights) and balanced accuracy. All metrics are reported with bootstrap 95 % confidence '
    'intervals (1,000 stratified resamples). Head-to-head comparisons between ML models and '
    'the IHC surrogate used the intersection of samples classifiable by both methods, ensuring '
    'identical denominators. Sensitivity analyses included: (a) 3-class analysis collapsing '
    'Luminal A and B into a single "Luminal" class; (b) grey-zone analysis stratifying '
    'predictions by maximum predicted class probability into low (< 0.50), medium (0.50-0.70), '
    'and high (> 0.70) confidence bins. All analyses were performed in Python 3.13 with '
    'scikit-learn and XGBoost.')

# ============================================================
# 3. RESULTS
# ============================================================
pdf.h1('3. Results')

pdf.h2('3.1 Cohort Characteristics')
pdf.p(
    'After exclusions, 5,377 tumours were analysed: 3,250 in the training set (GSE81538 + '
    'GSE96058) and 2,127 in external validation (TCGA-BRCA + METABRIC). Luminal A was the '
    'most prevalent subtype in every cohort (41-54 %), followed by Luminal B (24-30 %), '
    'Basal-like (11-19 %), and HER2-enriched (11-17 %). ER positivity ranged from 77 % to '
    '92 %; HER2 positivity from 13 % to 22 %. Median Ki-67 in GSE81538 was 20 % (IQR 10-30). '
    'Histological grade distribution was comparable across the three cohorts where it was '
    'available (Table 1, Figure 2).')

# Figure 2 -- cohort characteristics
pdf.fig(os.path.join(FIG_DIR, 'fig2_cohort.png'),
    'Figure 2. Cohort characteristics. (A) PAM50 subtype distribution by cohort. '
    '(B) ER and HER2 positivity rates. (C) Histological grade distribution. '
    '(D) Ki-67 distribution by subtype (GSE81538 only). '
    '(E) Sample sizes per cohort. (F) Missing-data pattern.',
    w=165)

pdf.h2('3.2 IHC Surrogate Performance and Luminal Crossover')
pdf.p(
    'The IHC surrogate was classifiable for 4,694 of 5,377 tumours (87.3 %). On METABRIC '
    '(head-to-head n = 1,554), it achieved macro-F1 = 0.646 (95 % CI 0.623-0.669) and '
    'kappa = 0.471 (0.436-0.506). Concordance was highest for Basal-like and HER2-enriched '
    'subtypes but markedly lower for luminal tumours. The Luminal A/B crossover was the '
    'dominant error: 42.5 % of molecular Luminal B cases received a Luminal A-like surrogate '
    'label, while 26.9 % of Luminal A cases were over-classified as Luminal B-like (Table 2). '
    'This pattern was consistent across all four cohorts.')

pdf.small_table(t_lumab,
    'Table 2. Luminal A/B crossover: proportion of molecular subtypes misclassified by the IHC surrogate.')

pdf.h2('3.3 ML Classifiers vs. IHC Surrogate -- Head-to-Head')
pdf.p(
    'No ML model outperformed the IHC surrogate in any head-to-head comparison (Figure 3). '
    'On METABRIC (n = 1,554), the best Set 1 model (XGBoost) reached macro-F1 = 0.523 '
    '(0.503-0.544) vs. surrogate 0.646. Adding grade (Set 2, n = 1,544) improved XGBoost to '
    '0.559 (0.533-0.584) vs. surrogate 0.644 (0.616-0.669). On TCGA-BRCA (n = 162), the '
    'surrogate achieved 0.485 (0.431-0.541) vs. best ML 0.368. The confidence intervals of '
    'the best ML models did not overlap with those of the surrogate in METABRIC, confirming a '
    'statistically significant disadvantage.')

# Figure 3 -- forest plot
pdf.fig(os.path.join(FIG_DIR, 'fig3_forest.png'),
    'Figure 3. Forest plot of macro-F1 scores with bootstrap 95 % CIs. '
    'Red markers: IHC surrogate. Blue markers: ML models. '
    'Squares denote head-to-head comparisons on identical sample subsets.',
    w=165)

pdf.h2('3.4 Confusion Matrix Analysis')
pdf.p(
    'Normalised confusion matrices on METABRIC (Figure 4) reveal complementary error patterns. '
    'The IHC surrogate correctly identifies Basal-like and HER2-enriched cases with high '
    'sensitivity (> 0.75) but cannot separate Luminal A from Luminal B: roughly 40 % of '
    'predictions in each luminal class are swapped. XGBoost (Set 2) partially improves '
    'Luminal B detection at the cost of reduced Luminal A specificity, indicating a trade-off '
    'rather than a net gain in information.')

# Figure 4 -- confusion matrices
pdf.fig(os.path.join(FIG_DIR, 'fig4_confusion.png'),
    'Figure 4. Normalised confusion matrices on METABRIC. '
    '(A) IHC surrogate. (B) XGBoost Set 1 (ER, PR, HER2). (C) XGBoost Set 2 (+ grade). '
    'Row-normalised proportions; darker cells = higher concordance.',
    w=170)

pdf.h2('3.5 Grey-Zone Analysis')
pdf.p(
    'Stratifying METABRIC predictions by the maximum predicted class probability revealed a '
    'clear confidence-accuracy gradient (Figure 5, Table 3). In the low-confidence zone '
    '(max probability < 0.50), comprising 13.5 % of cases (n = 208), ML accuracy was only '
    '15.9 % while the surrogate still achieved 54.8 %. These cases were predominantly luminal '
    '(73.6 %). In the high-confidence zone (> 0.70, 58.2 % of cases), both methods performed '
    'comparably (ML 73.1 %, surrogate 73.8 %). The grey zone thus identifies the specific '
    'patient subgroup -- mainly HR+/HER2- -- where neither routine approach is reliable and '
    'molecular testing is most needed.')

# Figure 5 -- grey zone
pdf.fig(os.path.join(FIG_DIR, 'fig5_greyzone.png'),
    'Figure 5. Grey-zone analysis on METABRIC. (A) Distribution of maximum predicted '
    'probability, coloured by prediction correctness. (B) Accuracy by confidence bin for ML '
    'and surrogate. (C) PAM50 subtype composition within each confidence zone.',
    w=165)

pdf.small_table(t_gz,
    'Table 3. Grey-zone analysis: accuracy of ML and surrogate by prediction confidence tier.')

pdf.h2('3.6 Sensitivity Analysis: 3-Class Collapse')
pdf.p(
    'Collapsing Luminal A and B into a single "Luminal" class (3-class analysis) raised '
    'XGBoost macro-F1 from 0.514 to 0.777 on TCGA-BRCA and from 0.522 to 0.767 on METABRIC '
    '(Table 4). This confirms that effectively all of the classification deficit resides at '
    'the Luminal A/B boundary; the three broad biological groups (Luminal, HER2-enriched, '
    'Basal-like) are well separated by routine IHC alone.')

pdf.small_table(t_sens,
    'Table 4. Sensitivity analysis: 4-class versus 3-class (Luminal A + B grouped) '
    'performance on external validation.')

pdf.h2('3.7 Feature Importance')
pdf.p(
    'XGBoost feature importance (gain) confirmed ER status as the dominant predictor, followed '
    'by HER2, grade, Ki-67, and PR (Figure 6). This hierarchy mirrors known breast cancer '
    'biology: ER separates luminal from non-luminal; HER2 identifies the HER2-enriched '
    'subtype; proliferation markers attempt -- and largely fail -- to separate Luminal A from '
    'Luminal B.')

# Figure 6 -- feature importance
pdf.fig(os.path.join(FIG_DIR, 'fig6_importance.png'),
    'Figure 6. XGBoost feature importance (gain) by feature set. '
    'ER is the dominant predictor; proliferation markers (Ki-67, grade) contribute modestly.',
    w=100)

# ============================================================
# 4. DISCUSSION
# ============================================================
pdf.h1('4. Discussion')

pdf.p(
    'This multicohort in silico study demonstrates that routine pathology variables impose a '
    'hard information ceiling on the recoverability of 4-class PAM50 intrinsic subtypes. '
    'Three findings frame this conclusion.')

pdf.h2('4.1 ML Cannot Outperform the IHC Surrogate')
pdf.p(
    'Across every external-validation scenario, the best ML classifier fell short of the '
    'rule-based IHC surrogate. This is not a failure of the algorithms; it is evidence that '
    'the input variables -- binary ER, PR, HER2, plus ordinal grade -- do not contain enough '
    'discriminative information for reliable 4-class separation. With only three binary IHC '
    'markers, there are 2^3 = 8 possible input combinations to map to four output classes. '
    'Adding grade (3 levels) raises this to 24 combinations -- still a profoundly '
    'under-determined mapping. The IHC surrogate, built on decades of clinical refinement, '
    'already extracts most of the recoverable signal from these variables.')

pdf.h2('4.2 The Luminal A/B Boundary Is the Bottleneck')
pdf.p(
    'The Luminal A/B distinction accounts for virtually all of the classification deficit. '
    'Collapsing the two luminal classes into one raised macro-F1 from ~0.52 to ~0.77. '
    'Biologically, the PAM50 Luminal A/B boundary reflects a continuous proliferative axis '
    'best captured by a coordinated shift across dozens of cell-cycle genes [1]. Ki-67, a '
    'single immunohistochemical marker of proliferation, and histological grade, a 3-level '
    'ordinal summary of differentiation, are crude proxies for this continuous gene-expression '
    'signal. Our data confirm that even when both are available, the information gap cannot be '
    'closed by algorithmic means.')

pdf.h2('4.3 Clinical Implications: A Grey-Zone Framework')
pdf.p(
    'The grey-zone analysis translates the information ceiling into a clinically actionable '
    'framework. Approximately 14 % of cases fall into a low-confidence zone (max predicted '
    'probability < 0.50) characterised by near-random ML accuracy (16 %) and 74 % luminal '
    'composition. These are precisely the HR+/HER2- patients for whom the Luminal A vs. B '
    'distinction drives adjuvant chemotherapy decisions. Our findings support a selective '
    'testing strategy: patients with clear non-luminal phenotypes (triple-negative, HER2+) can '
    'be reliably classified by IHC alone (> 80 % concordance), while the luminal grey zone '
    'is where molecular testing adds the greatest incremental value.')

pdf.h2('4.4 Relation to Prior Work')
pdf.p(
    'Previous studies have reported ML models achieving higher concordance with PAM50 [10,11], '
    'but most used internal cross-validation rather than strict external validation, and few '
    'compared head-to-head with the IHC surrogate on identical samples. Our design -- external '
    'cohorts, matched denominators, bootstrap CIs -- provides a more rigorous test. The '
    'consistent finding across two independent validation cohorts (microarray-based METABRIC '
    'and RNA-seq-based TCGA) strengthens the generalisability of the information-ceiling '
    'interpretation.')

pdf.h2('4.5 Strengths and Limitations')
pdf.p(
    'Strengths: (i) four independent cohorts spanning two platforms (RNA-seq, microarray); '
    '(ii) head-to-head comparisons on identical sample subsets ensuring fair denominators; '
    '(iii) bootstrap 95 % CIs on all metrics; (iv) a grey-zone framework linking prediction '
    'uncertainty to clinical actionability.')

pdf.p(
    'Limitations: (i) IHC data were available only as binary (positive/negative) in most '
    'cohorts -- continuous measures (ER %, H-score) might improve models; '
    '(ii) continuous Ki-67 was available only in GSE81538 (n = 383); '
    '(iii) histological grade was absent in TCGA-BRCA, limiting Set 2 evaluation to METABRIC; '
    '(iv) PAM50 labels derive from heterogeneous implementations across studies; '
    '(v) no clinical outcome data were available to confirm the prognostic impact of grey-zone '
    'misclassification.')

# ============================================================
# 5. CONCLUSIONS
# ============================================================
pdf.h1('5. Conclusions')

pdf.p(
    'Routine clinicopathological variables define an information ceiling that prevents reliable '
    'reproduction of 4-class PAM50 intrinsic subtypes. Machine-learning classifiers cannot '
    'surpass the conventional IHC surrogate because the input data, not the algorithm, are the '
    'limiting factor. The irreducible uncertainty concentrates at the Luminal A/B boundary, '
    'identifying a grey zone comprising ~14 % of breast cancers where molecular testing is '
    'most likely to change clinical management. These findings argue against the expectation '
    'that software alone can replace gene-expression profiling, and support a stratified '
    'approach in which molecular subtyping resources are targeted to the patient subgroup '
    'where they provide the greatest clinical yield.')

# ============================================================
# DATA AVAILABILITY
# ============================================================
pdf.h1('Data Availability')
pdf.p(
    'All data used in this study are publicly available. GSE81538 and GSE96058 are deposited '
    'at NCBI GEO; TCGA-BRCA and METABRIC clinical data are available through cBioPortal. '
    'Analysis code is available upon request.')

# ============================================================
# REFERENCES
# ============================================================
pdf.h1('References')
pdf.set_font('Helvetica', '', 7.5)
refs = [
    '1. Parker JS et al. Supervised risk predictor of breast cancer based on intrinsic subtypes. J Clin Oncol 2009;27:1160-7.',
    '2. Perou CM et al. Molecular portraits of human breast tumours. Nature 2000;406:747-52.',
    '3. Prat A et al. Clinical implications of the intrinsic molecular subtypes of breast cancer. Breast 2015;24(Suppl 2):S26-35.',
    '4. Goldhirsch A et al. Personalizing the treatment of women with early breast cancer: highlights of the St Gallen 2013 consensus. Ann Oncol 2013;24:2206-23.',
    '5. Bastien RR et al. PAM50 breast cancer subtyping by RT-qPCR and concordance with standard clinical molecular markers. BMC Med Genomics 2012;5:44.',
    '6. Prat A et al. Prognostic significance of progesterone receptor-positive tumor cells within immunohistochemically defined luminal A breast cancer. J Clin Oncol 2013;31:203-9.',
    '7. Brueffer C et al. Clinical value of RNA sequencing-based classifiers for prediction of the five conventional breast cancer biomarkers: a SCAN-B report. JCO Precis Oncol 2018;2:1-18.',
    '8. Cancer Genome Atlas Network. Comprehensive molecular portraits of human breast tumours. Nature 2012;490:61-70.',
    '9. Curtis C et al. The genomic and transcriptomic architecture of 2,000 breast tumours reveals novel subgroups. Nature 2012;486:346-52.',
    '10. Chia SK et al. A 50-gene intrinsic subtype classifier for prognosis and prediction of benefit from adjuvant tamoxifen. Clin Cancer Res 2012;18:4465-72.',
    '11. Netanely D et al. Expression and methylation patterns partition luminal-A breast tumors into distinct prognostic subgroups. Breast Cancer Res 2016;18:74.',
]
for ref in refs:
    pdf.multi_cell(0, 3.5, ref)
    pdf.ln(0.5)

# ============================================================
# SAVE
# ============================================================
pdf_path = os.path.join(MS_DIR, "manuscript_final.pdf")
pdf.output(pdf_path)
print(f"Manuscript saved: {pdf_path}")
print(f"Size: {os.path.getsize(pdf_path)/1024:.0f} KB, Pages: {pdf.page_no()}")
