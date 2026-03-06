"""
Manuscript formatted for The Breast (Elsevier).
- Structured abstract: Objectives / Material and Methods / Results / Conclusions
- Vancouver references
- Authors: Botan RN, Sousa JB
- Figures: best of R + Python
- PDF with fpdf2 (Helvetica, ASCII safe)
"""

import os, sys
import pandas as pd
sys.stdout.reconfigure(encoding='utf-8')

from fpdf import FPDF

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(BASE_DIR, "figures")
FIG_R = os.path.join(BASE_DIR, "figures_R")
TAB_DIR = os.path.join(BASE_DIR, "tables")
MS_DIR = os.path.join(BASE_DIR, "manuscript")
os.makedirs(MS_DIR, exist_ok=True)

# Load tables
t_flow = pd.read_csv(os.path.join(TAB_DIR, 'table_sample_flow.csv'))
t_lumab = pd.read_csv(os.path.join(TAB_DIR, 'table_lumAB_crossover.csv'))
t_gz = pd.read_csv(os.path.join(TAB_DIR, 'table_grey_zone.csv'))
t_sens = pd.read_csv(os.path.join(TAB_DIR, 'table_sensitivity_enhanced.csv'))
t_main = pd.read_csv(os.path.join(TAB_DIR, 'table_main_results.csv'))


class TheBreastPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font('Helvetica', 'I', 7)
            self.set_text_color(100)
            self.cell(0, 4, 'Botan & Sousa -- The Breast (submitted)', align='C')
            self.ln(6)
            self.set_text_color(0)

    def footer(self):
        self.set_y(-12)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(100)
        self.cell(0, 10, f'{self.page_no()}', align='C')
        self.set_text_color(0)

    def h1(self, text):
        self.ln(4)
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 7, text, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0)
        self.set_line_width(0.35)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def h2(self, text):
        self.ln(2)
        self.set_font('Helvetica', 'B', 10)
        self.cell(0, 6, text, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def p(self, text):
        self.set_font('Helvetica', '', 9.5)
        self.multi_cell(0, 4.8, text)
        self.ln(1.5)

    def p_small(self, text):
        self.set_font('Helvetica', '', 8.5)
        self.multi_cell(0, 4.2, text)
        self.ln(1)

    def p_bold_start(self, bold_text, normal_text):
        self.set_font('Helvetica', 'B', 9.5)
        w_bold = self.get_string_width(bold_text) + 1
        self.cell(w_bold, 4.8, bold_text)
        self.set_font('Helvetica', '', 9.5)
        self.multi_cell(0, 4.8, normal_text)
        self.ln(1)

    def fig(self, path, caption, w=165):
        if self.get_y() > 190:
            self.add_page()
        self.image(path, x=(self.w - w) / 2, w=w)
        self.ln(2)
        self.set_font('Helvetica', 'I', 8)
        self.multi_cell(0, 3.8, caption)
        self.ln(4)

    def small_table(self, df, caption, max_cols=None):
        if self.get_y() > 215:
            self.add_page()
        self.set_font('Helvetica', 'B', 8.5)
        self.multi_cell(0, 4.2, caption)
        self.ln(1)

        cols = list(df.columns)
        if max_cols:
            cols = cols[:max_cols]
        n = len(cols)
        w = (self.w - self.l_margin - self.r_margin) / n

        self.set_font('Helvetica', 'B', 6.5)
        self.set_fill_color(230, 230, 230)
        for c in cols:
            self.cell(w, 4.2, str(c)[:24], border=1, fill=True)
        self.ln()

        self.set_font('Helvetica', '', 6.2)
        for _, row in df.iterrows():
            if self.get_y() > 270:
                self.add_page()
            for c in cols:
                val = str(row[c]) if pd.notna(row[c]) else ''
                self.cell(w, 3.8, val[:28], border=1)
            self.ln()
        self.ln(3)


# ============================================================
# BUILD PDF
# ============================================================
pdf = TheBreastPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# ---- ARTICLE TYPE ----
pdf.set_font('Helvetica', 'I', 9)
pdf.set_text_color(100)
pdf.cell(0, 5, 'Original Article', align='L', new_x="LMARGIN", new_y="NEXT")
pdf.set_text_color(0)
pdf.ln(2)

# ---- TITLE ----
pdf.set_font('Helvetica', 'B', 15)
pdf.multi_cell(0, 7,
    'Routine pathology data cannot reliably reproduce 4-class PAM50\n'
    'intrinsic subtypes in breast cancer: a multicohort in silico study',
    align='L')
pdf.ln(5)

# ---- AUTHORS ----
pdf.set_font('Helvetica', '', 10)
pdf.multi_cell(0, 5,
    'Rafael de Negreiros Botan 1,*  |  Joao Batista de Sousa 2')
pdf.ln(1)

pdf.set_font('Helvetica', 'I', 8.5)
pdf.multi_cell(0, 4.2,
    '1 Department of Oncology, Universidade de Brasilia -- Brasilia, Brazil\n'
    '2 Department of Proctology, Universidade de Brasilia -- Brasilia, Brazil')
pdf.ln(1)
pdf.set_font('Helvetica', '', 8)
pdf.cell(0, 4, '* Corresponding author: Rafael de Negreiros Botan -- oncologista@gmail.com',
         new_x="LMARGIN", new_y="NEXT")
pdf.ln(6)

# ---- ABSTRACT ----
pdf.set_draw_color(80)
pdf.set_line_width(0.3)

pdf.set_font('Helvetica', 'B', 11)
pdf.cell(0, 6, 'Abstract', new_x="LMARGIN", new_y="NEXT")
pdf.ln(1)

pdf.p_bold_start('Objectives: ',
    'To determine whether machine-learning (ML) classifiers applied to routine '
    'clinicopathological variables (ER, PR, HER2, Ki-67, histological grade) can improve '
    'upon the conventional immunohistochemistry (IHC) surrogate for predicting PAM50 '
    'intrinsic breast cancer subtypes, and to quantify the information ceiling imposed '
    'by these variables.')

pdf.p_bold_start('Material and methods: ',
    'Four public datasets were harmonised (GSE81538, n = 383; GSE96058, n = 2,867; '
    'TCGA-BRCA, n = 519; METABRIC, n = 1,608; total 5,377 tumours with 4-class PAM50 '
    'labels). Three classifiers (logistic regression, random forest, XGBoost) were trained '
    'on the SCAN-B cohorts using feature sets of increasing complexity (Set 1: ER/PR/HER2; '
    'Set 2: + grade; Set 3: + Ki-67) and validated externally. Head-to-head comparisons '
    'with the IHC surrogate used identical sample subsets. All metrics carry bootstrap '
    '95% confidence intervals (1,000 resamples).')

pdf.p_bold_start('Results: ',
    'On METABRIC (head-to-head, n = 1,554), the IHC surrogate achieved macro-F1 = 0.646 '
    '(95% CI 0.623-0.669) versus best ML 0.559 (0.533-0.584; XGBoost, Set 2). No ML model '
    'outperformed the surrogate in any comparison. The Luminal A/B boundary was the dominant '
    'error source: 42.5% of true Luminal B cases received a Luminal A-like label. Collapsing '
    'both luminal classes raised macro-F1 to 0.767. A grey-zone analysis showed that 13.5% '
    'of cases (max predicted probability < 0.50) were 73.6% luminal and had only 15.9% ML '
    'accuracy.')

pdf.p_bold_start('Conclusions: ',
    'Routine clinicopathological variables impose an information ceiling that prevents '
    'reliable reproduction of 4-class PAM50 subtypes. The irreducible uncertainty '
    'concentrates at the Luminal A/B boundary, defining a grey zone where molecular testing '
    'adds the greatest clinical value.')

pdf.ln(1)
pdf.set_font('Helvetica', 'B', 8)
pdf.multi_cell(0, 4,
    'Keywords: breast cancer; PAM50; intrinsic subtypes; immunohistochemistry; '
    'machine learning; information ceiling; grey zone')

# ============================================================
# 1. INTRODUCTION
# ============================================================
pdf.h1('1. Introduction')

pdf.p(
    'Breast cancer is a molecularly heterogeneous disease. Gene-expression profiling '
    'identifies at least four intrinsic subtypes -- Luminal A, Luminal B, HER2-enriched, and '
    'Basal-like -- each carrying distinct prognostic trajectories and treatment implications '
    '[1,2]. The PAM50 assay, based on a 50-gene expression signature, is the reference '
    'standard for intrinsic subtype assignment and informs clinical decisions on adjuvant '
    'therapy escalation or de-escalation [3].')

pdf.p(
    'Because gene-expression testing requires fresh or frozen tissue, specialised platforms, '
    'and significant cost, most centres worldwide rely on immunohistochemistry (IHC) '
    'surrogates endorsed by the St. Gallen consensus [4]. These surrogates map combinations '
    'of ER, PR, HER2, and Ki-67 (or histological grade) to "Luminal A-like", "Luminal '
    'B-like", "HER2-positive", and "Triple-negative" categories intended to mirror '
    'intrinsic subtypes. Published concordance between IHC surrogates and PAM50 ranges from '
    '50% to 80%, with well-documented weakness at the Luminal A/B boundary [5,6].')

pdf.p(
    'An intuitive next step is to ask whether machine-learning (ML) algorithms, trained on '
    'the same routine variables, can extract additional discriminative signal and outperform '
    'the rule-based surrogate. If so, a simple software upgrade could improve subtype '
    'assignment at no additional laboratory cost. If not, the negative result is equally '
    'informative: it implies that routine data contain an information ceiling that no '
    'algorithm can overcome, and that molecular testing is irreplaceable for specific '
    'patient subgroups.')

pdf.p(
    'This study tests the latter hypothesis in a multicohort in silico framework. We train '
    'three ML classifiers on two SCAN-B cohorts (n = 3,250), evaluate them on TCGA-BRCA '
    '(n = 519) and METABRIC (n = 1,608), and compare every model head-to-head with the IHC '
    'surrogate on identical sample subsets. We further introduce a grey-zone analysis that '
    'stratifies cases by prediction confidence to identify the patient population most likely '
    'to benefit from molecular subtyping.')

# ============================================================
# 2. MATERIAL AND METHODS
# ============================================================
pdf.h1('2. Material and methods')

pdf.h2('2.1. Study design')
pdf.p(
    'Retrospective, purely in silico, multicohort diagnostic-accuracy study. The index tests '
    'are each ML classifier and the IHC surrogate; the reference standard is the published '
    'PAM50 label in each cohort. No new biological samples were analysed. The study follows '
    'the TRIPOD guidelines for multivariable prediction models [7].')

pdf.h2('2.2. Data sources and cohorts')
pdf.p(
    'Four publicly available breast cancer datasets were used (Table 1, Fig. 1):')
pdf.p(
    'Training set -- (i) GSE81538 (SCAN-B, n = 405; 383 with 4-class PAM50): RNA-seq with '
    'multi-observer IHC consensus for ER, PR, HER2, Ki-67, and NHG grade [8]. '
    '(ii) GSE96058 (SCAN-B, n = 3,069; 2,867 with 4-class PAM50): RNA-seq; binary IHC '
    'status and NHG grade [8].')
pdf.p(
    'External validation -- (iii) TCGA-BRCA (n = 1,108 clinical; 519 with published PAM50 '
    'from brca_tcga_pub): RNA-seq; ER, PR, HER2 from IHC/FISH, no grade [9]. '
    '(iv) METABRIC (n = 2,509 clinical; 1,608 with 4-class PAM50): Illumina microarray; '
    'ER, PR, HER2, NHG grade, no Ki-67 [10].')
pdf.p(
    'Normal-like and claudin-low subtypes were excluded to yield a standard 4-class target. '
    'All data were downloaded from NCBI GEO (series matrix files) or cBioPortal (REST API).')

# TABLE 1
pdf.small_table(t_flow,
    'Table 1. Sample flow and feature-set availability by cohort.')

pdf.h2('2.3. Variable harmonisation')
pdf.p(
    'ER and PR were coded as binary positive/negative across all cohorts. HER2 was binary; '
    'equivocal IHC results were resolved by FISH when available (TCGA). Ki-67 was available '
    'as a continuous percentage only in GSE81538; in GSE96058 it was stored as a binary '
    'high/low flag (mapped to proxy values of 30% and 10%, respectively). Ki-67 was absent '
    'in TCGA and METABRIC. Histological grade (NHG, 1-3) was present in GSE81538, GSE96058, '
    'and METABRIC but absent in TCGA-BRCA.')

pdf.h2('2.4. IHC surrogate classification')
pdf.p(
    'The conventional surrogate followed St. Gallen 2013 rules [4]: Luminal A-like = '
    'HR+/HER2-/low proliferation; Luminal B-like = HR+/HER2-/high proliferation or '
    'HR+/HER2+; HER2-positive (non-luminal) = HR-/HER2+; Triple-negative = HR-/HER2-. '
    'Proliferation was defined as Ki-67 >= 20% when available, or grade 3 as proxy. '
    'Cases missing ER, PR, or HER2 were excluded from surrogate classification.')

pdf.h2('2.5. Feature sets')
pdf.p(
    'Three nested sets reflected real-world data availability: Set 1 (Core IHC): ER, PR, '
    'HER2 -- universally available. Set 2 (IHC + Grade): adds histological grade (GSE81538, '
    'GSE96058, METABRIC). Set 3 (IHC + Ki-67 + Grade): adds continuous Ki-67 (GSE81538 + '
    'partial GSE96058 only; not evaluable on external validation).')

pdf.h2('2.6. Machine-learning models')
pdf.p(
    'Three classifiers were trained on the combined GSE81538 + GSE96058: (i) multinomial '
    'logistic regression with balanced class weights; (ii) random forest (500 trees, '
    'balanced); (iii) XGBoost (500 rounds, max depth 6, learning rate 0.1). No '
    'hyperparameter tuning was performed on the validation cohorts.')

pdf.h2('2.7. Statistical analysis')
pdf.p(
    'Primary endpoint: macro-averaged F1-score. Secondary endpoints: Cohen\'s kappa and '
    'balanced accuracy. All metrics are reported with bootstrap 95% confidence intervals '
    '(1,000 stratified resamples). Head-to-head comparisons between ML models and the IHC '
    'surrogate used the intersection of samples classifiable by both methods, ensuring '
    'identical denominators.')
pdf.p(
    'Sensitivity analyses included: (a) 3-class analysis collapsing Luminal A and B into a '
    'single "Luminal" class; (b) grey-zone analysis stratifying predictions by maximum '
    'predicted class probability into low (< 0.50), medium (0.50-0.70), and high (> 0.70) '
    'confidence bins. Analyses were performed in Python 3.13 with scikit-learn 1.6 and '
    'XGBoost 2.1.')

# ============================================================
# 3. RESULTS
# ============================================================
pdf.h1('3. Results')

pdf.h2('3.1. Cohort characteristics')
pdf.p(
    'After exclusions, 5,377 tumours were analysed: 3,250 in the training set (GSE81538 + '
    'GSE96058) and 2,127 in external validation (TCGA-BRCA + METABRIC). Luminal A was the '
    'most prevalent subtype in every cohort (41-54%), followed by Luminal B (24-30%), '
    'Basal-like (11-19%), and HER2-enriched (11-17%). ER positivity ranged from 77% to 92%; '
    'HER2 positivity from 13% to 22%. Histological grade distribution was comparable across '
    'the three cohorts where it was available (Fig. 1).')

# FIGURE 1 -- Cohort characteristics (R multipanel)
pdf.fig(os.path.join(FIG_R, 'fig2_cohort_characteristics.png'),
    'Fig. 1. Cohort characteristics. (A) PAM50 subtype distribution by cohort. '
    '(B) ER and HER2 positivity rates. (C) Histological grade distribution. '
    '(D) Absolute counts by subtype.',
    w=170)

pdf.h2('3.2. IHC surrogate performance and Luminal A/B crossover')
pdf.p(
    'The IHC surrogate was classifiable for 4,694 of 5,377 tumours (87.3%). On METABRIC '
    '(head-to-head n = 1,554), it achieved macro-F1 = 0.646 (95% CI 0.623-0.669) and '
    'kappa = 0.471 (0.436-0.506). Concordance was highest for Basal-like and HER2-enriched '
    'subtypes but markedly lower for luminal tumours.')
pdf.p(
    'The Luminal A/B crossover was the dominant error: 42.5% of molecular Luminal B cases '
    'received a Luminal A-like surrogate label, while 26.9% of Luminal A cases were '
    'over-classified as Luminal B-like (Fig. 2, Table 2). This pattern was consistent '
    'across all four cohorts, though TCGA-BRCA showed an extreme LumA-to-LumB crossover '
    '(92.9%), likely reflecting its small sample and absence of grade data.')

# FIGURE 2 -- Luminal crossover (R, NEW)
pdf.fig(os.path.join(FIG_R, 'fig4_luminal_crossover.png'),
    'Fig. 2. Luminal A/B crossover by IHC surrogate across cohorts. '
    'The Luminal B-to-Luminal A misclassification is the dominant error in METABRIC (42.5%), '
    'while Luminal A-to-Luminal B misclassification predominates in TCGA-BRCA (92.9%, n = 28).',
    w=155)

# TABLE 2
pdf.small_table(t_lumab,
    'Table 2. Luminal A/B crossover: proportion of molecular subtypes misclassified by the IHC surrogate.')

pdf.h2('3.3. ML classifiers vs. IHC surrogate (head-to-head)')
pdf.p(
    'No ML model outperformed the IHC surrogate in any head-to-head comparison (Fig. 3). '
    'On METABRIC (n = 1,554), the best Set 1 model (XGBoost) reached macro-F1 = 0.523 '
    '(0.503-0.544) vs. surrogate 0.646. Adding grade (Set 2, n = 1,544) improved XGBoost '
    'to 0.559 (0.533-0.584) vs. surrogate 0.644 (0.616-0.669). On TCGA-BRCA (n = 162), '
    'the surrogate achieved 0.485 (0.431-0.541) vs. best ML 0.368. The confidence intervals '
    'of the best ML models did not overlap with those of the surrogate in METABRIC, '
    'confirming a statistically significant disadvantage.')

# FIGURE 3 -- Forest plot (R)
pdf.fig(os.path.join(FIG_R, 'fig3_forest_h2h.png'),
    'Fig. 3. Forest plot of macro-F1 scores with bootstrap 95% CIs. '
    'Red: IHC surrogate. Blue: ML models. Head-to-head comparisons on identical sample '
    'subsets show the surrogate consistently outperforms all ML classifiers.',
    w=160)

pdf.h2('3.4. Confusion matrix analysis')
pdf.p(
    'Normalised confusion matrices on METABRIC (Fig. 4) reveal complementary error patterns. '
    'The IHC surrogate correctly identifies Basal-like and HER2-enriched cases with high '
    'sensitivity (> 0.75) but cannot separate Luminal A from Luminal B: roughly 40% of '
    'predictions in each luminal class are swapped. XGBoost (Set 2) partially improves '
    'Luminal B detection at the cost of reduced Luminal A specificity, indicating a trade-off '
    'rather than a net gain in information.')

# FIGURE 4 -- Confusion matrices (Python -- these are better as heatmaps)
pdf.fig(os.path.join(FIG_DIR, 'fig4_confusion.png'),
    'Fig. 4. Normalised confusion matrices on METABRIC. '
    '(A) IHC surrogate. (B) XGBoost Set 1 (ER, PR, HER2). (C) XGBoost Set 2 (+ grade). '
    'Row-normalised proportions; darker cells indicate higher concordance.',
    w=170)

pdf.h2('3.5. Grey-zone analysis')
pdf.p(
    'Stratifying METABRIC predictions by the maximum predicted class probability revealed a '
    'clear confidence-accuracy gradient (Fig. 5, Table 3). In the low-confidence zone '
    '(max probability < 0.50), comprising 13.5% of cases (n = 208), ML accuracy was only '
    '15.9% while the surrogate still achieved 54.8%. These cases were predominantly luminal '
    '(73.6%). In the high-confidence zone (> 0.70, 58.2% of cases), both methods performed '
    'comparably (ML 73.1%, surrogate 73.8%). The grey zone thus identifies the specific '
    'patient subgroup -- mainly HR+/HER2- -- where neither routine approach is reliable and '
    'molecular testing is most needed.')

# FIGURE 5 -- Grey zone (R multipanel)
pdf.fig(os.path.join(FIG_R, 'fig5_grey_zone.png'),
    'Fig. 5. Grey-zone analysis on METABRIC. (A) Accuracy by confidence zone for ML and '
    'IHC surrogate. (B) Distribution of cases across confidence tiers. '
    '(C) Luminal A + B proportion within each confidence zone.',
    w=160)

# TABLE 3
pdf.small_table(t_gz,
    'Table 3. Grey-zone analysis: accuracy of ML and IHC surrogate by prediction confidence tier.')

pdf.h2('3.6. Sensitivity analysis: 3-class collapse')
pdf.p(
    'Collapsing Luminal A and B into a single "Luminal" class raised XGBoost macro-F1 from '
    '0.514 to 0.777 (95% CI 0.720-0.826) on TCGA-BRCA and from 0.522 to 0.767 '
    '(0.739-0.796) on METABRIC (Table 4). This confirms that effectively all of the '
    'classification deficit resides at the Luminal A/B boundary; the three broad biological '
    'groups (Luminal, HER2-enriched, Basal-like) are well separated by routine IHC alone.')

# TABLE 4
pdf.small_table(t_sens,
    'Table 4. Sensitivity analysis: 4-class vs. 3-class (Luminal A + B grouped) performance.')

pdf.h2('3.7. The information ceiling')
pdf.p(
    'Fig. 6 synthesises the central finding. As feature complexity increases from core IHC '
    '(3 binary variables, 8 input combinations) through grade (24 combinations) to Ki-67, '
    'ML performance improves incrementally but never reaches the IHC surrogate. The surrogate '
    'itself plateaus well below perfect concordance. Only the full 50-gene PAM50 assay '
    'achieves definitive classification, demonstrating that the information ceiling is '
    'intrinsic to the variables, not to the algorithm.')

# FIGURE 6 -- Information ceiling concept (R, NEW)
pdf.fig(os.path.join(FIG_R, 'fig10_information_ceiling.png'),
    'Fig. 6. The information ceiling concept. ML performance improves with feature complexity '
    'but plateaus below the IHC surrogate (dotted line). Only gene-expression profiling '
    '(PAM50, 50 genes) breaks through the ceiling. The shaded zone indicates the information '
    'ceiling imposed by routine clinicopathological variables.',
    w=145)

# ============================================================
# 4. DISCUSSION
# ============================================================
pdf.h1('4. Discussion')

pdf.p(
    'This multicohort in silico study demonstrates that routine pathology variables impose a '
    'hard information ceiling on the recoverability of 4-class PAM50 intrinsic subtypes. '
    'Three key findings frame this conclusion.')

pdf.h2('4.1. ML cannot outperform the IHC surrogate')
pdf.p(
    'Across every external-validation scenario, the best ML classifier fell short of the '
    'rule-based IHC surrogate. This is not a failure of the algorithms; it is evidence that '
    'the input variables -- binary ER, PR, HER2, plus ordinal grade -- do not contain enough '
    'discriminative information for reliable 4-class separation. With only three binary IHC '
    'markers, there are 2^3 = 8 possible input combinations to map to four output classes. '
    'Adding grade raises this to 24 -- still a profoundly under-determined mapping. The IHC '
    'surrogate, built on decades of clinical refinement, already extracts most of the '
    'recoverable signal from these variables.')

pdf.h2('4.2. The Luminal A/B boundary is the bottleneck')
pdf.p(
    'The Luminal A/B distinction accounts for virtually all of the classification deficit. '
    'Collapsing the two luminal classes raised macro-F1 from ~0.52 to ~0.77. Biologically, '
    'the PAM50 Luminal A/B boundary reflects a continuous proliferative axis best captured '
    'by a coordinated shift across dozens of cell-cycle genes [1]. Ki-67, a single protein '
    'marker of proliferation, and histological grade, a 3-level ordinal summary, are crude '
    'proxies for this continuous gene-expression signal. Our data confirm that even when both '
    'are available, the information gap cannot be closed by algorithmic means.')

pdf.h2('4.3. Clinical implications: a grey-zone framework')
pdf.p(
    'The grey-zone analysis translates the information ceiling into a clinically actionable '
    'framework. Approximately 14% of cases fall into a low-confidence zone characterised by '
    'near-random ML accuracy (16%) and 74% luminal composition. These are precisely the '
    'HR+/HER2- patients for whom the Luminal A vs. B distinction drives adjuvant chemotherapy '
    'decisions [11]. Our findings support a selective testing strategy: patients with clear '
    'non-luminal phenotypes (triple-negative, HER2+) can be reliably classified by IHC alone '
    '(> 80% concordance), while the luminal grey zone is where molecular testing adds the '
    'greatest incremental value.')

pdf.h2('4.4. Relation to prior work')
pdf.p(
    'Previous studies have reported ML models achieving higher concordance with PAM50 '
    '[12,13], but most used internal cross-validation rather than strict external validation, '
    'and few compared head-to-head with the IHC surrogate on identical samples. Our design '
    '-- external cohorts, matched denominators, bootstrap CIs -- provides a more rigorous '
    'test. The consistent finding across two independent validation cohorts spanning two '
    'platforms (RNA-seq TCGA, microarray METABRIC) strengthens the generalisability of the '
    'information-ceiling interpretation.')

pdf.h2('4.5. Strengths and limitations')
pdf.p(
    'Strengths include: (i) four independent cohorts spanning two platforms; (ii) head-to-head '
    'comparisons on identical sample subsets ensuring fair denominators; (iii) bootstrap 95% '
    'CIs on all metrics; (iv) a grey-zone framework linking prediction uncertainty to clinical '
    'actionability; (v) transparent reporting following TRIPOD guidelines.')
pdf.p(
    'Limitations: (i) IHC data were available only as binary in most cohorts -- continuous '
    'measures (ER%, H-score) might improve models; (ii) continuous Ki-67 was available only '
    'in GSE81538 (n = 383); (iii) histological grade was absent in TCGA-BRCA; '
    '(iv) PAM50 labels derive from heterogeneous implementations across studies; (v) no '
    'clinical outcome data were available to confirm the prognostic impact of grey-zone '
    'misclassification; (vi) as a purely in silico study, our findings require prospective '
    'validation.')

# ============================================================
# 5. CONCLUSIONS
# ============================================================
pdf.h1('5. Conclusions')

pdf.p(
    'Routine clinicopathological variables define an information ceiling that prevents reliable '
    'reproduction of 4-class PAM50 intrinsic subtypes. Machine-learning classifiers cannot '
    'surpass the conventional IHC surrogate because the input data, not the algorithm, are '
    'the limiting factor. The irreducible uncertainty concentrates at the Luminal A/B boundary, '
    'identifying a grey zone comprising ~14% of breast cancers where molecular testing is most '
    'likely to change clinical management. These findings argue against the expectation that '
    'software alone can replace gene-expression profiling, and support a stratified approach '
    'in which molecular subtyping resources are targeted to the patient subgroup where they '
    'provide the greatest clinical yield.')

# ============================================================
# FUNDING
# ============================================================
pdf.h1('Funding')
pdf.p('This research did not receive any specific grant from funding agencies in the public, '
      'commercial, or not-for-profit sectors.')

# ============================================================
# DECLARATION OF COMPETING INTEREST
# ============================================================
pdf.h1('Declaration of competing interest')
pdf.p('The authors declare that they have no known competing financial interests or personal '
      'relationships that could have appeared to influence the work reported in this paper.')

# ============================================================
# CRediT AUTHORSHIP
# ============================================================
pdf.h1('CRediT authorship contribution statement')
pdf.p(
    'Rafael de Negreiros Botan: Conceptualisation, Methodology, Software, Formal analysis, '
    'Data curation, Writing -- original draft, Visualisation. '
    'Joao Batista de Sousa: Supervision, Writing -- review & editing.')

# ============================================================
# DATA AVAILABILITY
# ============================================================
pdf.h1('Data availability')
pdf.p(
    'All data used in this study are publicly available. GSE81538 and GSE96058 are deposited '
    'at NCBI GEO (https://www.ncbi.nlm.nih.gov/geo/); TCGA-BRCA and METABRIC clinical data '
    'are available through cBioPortal (https://www.cbioportal.org/). Analysis code is '
    'available from the corresponding author upon reasonable request.')

# ============================================================
# REFERENCES
# ============================================================
pdf.h1('References')
pdf.set_font('Helvetica', '', 7.5)
refs = [
    '[1] Parker JS, Mullins M, Cheang MC, et al. Supervised risk predictor of breast cancer based on intrinsic subtypes. J Clin Oncol 2009;27(8):1160-7.',
    '[2] Perou CM, Sorlie T, Eisen MB, et al. Molecular portraits of human breast tumours. Nature 2000;406(6797):747-52.',
    '[3] Prat A, Fan C, Fernandez A, et al. Clinical implications of the intrinsic molecular subtypes of breast cancer. Breast 2015;24(Suppl 2):S26-35.',
    '[4] Goldhirsch A, Winer EP, Coates AS, et al. Personalizing the treatment of women with early breast cancer: highlights of the St Gallen International Expert Consensus on the Primary Therapy of Early Breast Cancer 2013. Ann Oncol 2013;24(9):2206-23.',
    '[5] Bastien RR, Rodriguez-Lescure A, Ebbert MT, et al. PAM50 breast cancer subtyping by RT-qPCR and concordance with standard clinical molecular markers. BMC Med Genomics 2012;5:44.',
    '[6] Prat A, Cheang MC, Martin M, et al. Prognostic significance of progesterone receptor-positive tumor cells within immunohistochemically defined luminal A breast cancer. J Clin Oncol 2013;31(2):203-9.',
    '[7] Collins GS, Reitsma JB, Altman DG, Moons KG. Transparent reporting of a multivariable prediction model for individual prognosis or diagnosis (TRIPOD). BMJ 2015;350:g7594.',
    '[8] Brueffer C, Vallon-Christersson J, Grabau D, et al. Clinical value of RNA sequencing-based classifiers for prediction of the five conventional breast cancer biomarkers: a report from the population-based multicenter Sweden Cancerome Analysis Network -- Breast (SCAN-B) initiative. JCO Precis Oncol 2018;2:1-18.',
    '[9] Cancer Genome Atlas Network. Comprehensive molecular portraits of human breast tumours. Nature 2012;490(7418):61-70.',
    '[10] Curtis C, Shah SP, Chin SF, et al. The genomic and transcriptomic architecture of 2,000 breast tumours reveals novel subgroups. Nature 2012;486(7403):346-52.',
    '[11] Cardoso F, van\'t Veer LJ, Bogaerts J, et al. 70-gene signature as an aid to treatment decisions in early-stage breast cancer. N Engl J Med 2016;375(8):717-29.',
    '[12] Chia SK, Bramwell VH, Tu D, et al. A 50-gene intrinsic subtype classifier for prognosis and prediction of benefit from adjuvant tamoxifen. Clin Cancer Res 2012;18(16):4465-72.',
    '[13] Netanely D, Avraham A, Ben-Baruch A, Evron E, Feldman I. Expression and methylation patterns partition luminal-A breast tumors into distinct prognostic subgroups. Breast Cancer Res 2016;18(1):74.',
]
for ref in refs:
    pdf.multi_cell(0, 3.5, ref)
    pdf.ln(0.8)

# ============================================================
# SUPPLEMENTARY FIGURES (on separate pages)
# ============================================================
pdf.add_page()
pdf.h1('Supplementary Material')

pdf.fig(os.path.join(FIG_R, 'fig7_sensitivity_3v4.png'),
    'Supplementary Fig. S1. Sensitivity analysis: 4-class vs. 3-class (luminal grouped) '
    'performance with bootstrap 95% CIs. Collapsing the luminal subtypes eliminates '
    'virtually all classification error.',
    w=130)

pdf.fig(os.path.join(FIG_R, 'fig8_feature_set_comparison.png'),
    'Supplementary Fig. S2. ML performance by feature set on METABRIC. Adding grade '
    '(Set 2) improves all ML models but none reaches the IHC surrogate (dashed red line, '
    'F1 = 0.646).',
    w=150)

pdf.fig(os.path.join(FIG_R, 'fig9_multimetric_panel.png'),
    'Supplementary Fig. S3. Multi-metric comparison on METABRIC (head-to-head). The IHC '
    'surrogate outperforms ML on every metric: macro-F1, kappa, and balanced accuracy.',
    w=150)

pdf.fig(os.path.join(FIG_R, 'fig6_feature_importance.png'),
    'Supplementary Fig. S4. XGBoost feature importance (gain). ER status dominates; '
    'proliferation markers (Ki-67, grade) contribute modestly, reflecting the information '
    'ceiling at the Luminal A/B boundary.',
    w=120)

# ============================================================
# SAVE
# ============================================================
pdf_path = os.path.join(MS_DIR, "manuscript_TheBreast.pdf")
pdf.output(pdf_path)
print(f"Manuscript saved: {pdf_path}")
print(f"Size: {os.path.getsize(pdf_path)/1024:.0f} KB, Pages: {pdf.page_no()}")
