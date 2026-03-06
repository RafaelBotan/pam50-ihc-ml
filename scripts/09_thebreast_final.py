"""
Final manuscript PDF for The Breast (Elsevier).
Uses the definitive user-written text + R figures (clean, no titles) + references.
ASCII-safe Helvetica via fpdf2.
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
pdf.set_font('Helvetica', 'B', 14)
pdf.multi_cell(0, 6.5,
    'Routine pathology cannot reliably reproduce 4-class PAM50 intrinsic\n'
    'subtypes in breast cancer: a multicohort in silico study defining\n'
    'the luminal grey zone', align='L')
pdf.ln(4)

# ---- AUTHORS ----
pdf.set_font('Helvetica', '', 10)
pdf.multi_cell(0, 5,
    'Rafael de Negreiros Botan 1,*   Joao Batista de Sousa 2')
pdf.ln(1)
pdf.set_font('Helvetica', 'I', 8.5)
pdf.multi_cell(0, 4.2,
    '1 Department of Oncology, Universidade de Brasilia, Brasilia, Brazil\n'
    '2 Department of Proctology, Universidade de Brasilia, Brasilia, Brazil')
pdf.ln(1)
pdf.set_font('Helvetica', '', 8)
pdf.cell(0, 4, '* Corresponding author: Rafael de Negreiros Botan -- oncologista@gmail.com',
         new_x="LMARGIN", new_y="NEXT")
pdf.ln(1)
pdf.set_font('Helvetica', 'I', 8)
pdf.cell(0, 4, 'Running title: Information ceiling for routine-data approximation of PAM50',
         new_x="LMARGIN", new_y="NEXT")
pdf.ln(1)
pdf.set_font('Helvetica', 'B', 8)
pdf.multi_cell(0, 4,
    'Keywords: breast cancer; PAM50; intrinsic subtype; immunohistochemistry; '
    'machine learning; grey zone')
pdf.ln(4)

# ---- ABSTRACT ----
pdf.set_font('Helvetica', 'B', 11)
pdf.cell(0, 6, 'Abstract', new_x="LMARGIN", new_y="NEXT")
pdf.ln(1)

pdf.p_bold_start('Background: ',
    'Immunohistochemistry-based surrogate classification is widely used to approximate '
    'intrinsic breast cancer subtypes in routine care, but its agreement with PAM50 is '
    'incomplete. We tested whether machine-learning models applied to routine '
    'clinicopathological variables could improve on the conventional surrogate and '
    'quantified the information ceiling imposed by these variables.')

pdf.p_bold_start('Methods: ',
    'Four public datasets with 4-class PAM50 labels were analysed (GSE81538, n=383; '
    'GSE96058, n=2,867; TCGA-BRCA, n=519; METABRIC, n=1,608; total n=5,377). Logistic '
    'regression, random forest, and XGBoost were trained on the SCAN-B cohorts using '
    'nested feature sets of increasing complexity: ER/PR/HER2 (Set 1), + grade (Set 2), '
    'and + Ki-67 (Set 3). External validation was performed in TCGA-BRCA and METABRIC. '
    'Head-to-head comparisons with the immunohistochemical surrogate used identical '
    'evaluable subsets, and performance was estimated with bootstrap 95% confidence intervals.')

pdf.p_bold_start('Results: ',
    'No machine-learning model outperformed the surrogate in any external comparison. '
    'On METABRIC head-to-head analysis (n=1,554), the surrogate achieved macro-F1 0.646 '
    '(95% CI 0.623-0.669) versus 0.559 (0.533-0.584) for the best model (XGBoost, Set 2). '
    'The dominant source of error was the Luminal A/Luminal B boundary: 42.5% of molecular '
    'Luminal B tumours received a Luminal A-like surrogate label. Collapsing both luminal '
    'classes increased macro-F1 to 0.767. A low-confidence grey zone comprised 13.5% of '
    'cases, was 73.6% luminal, and showed only 15.9% machine-learning accuracy.')

pdf.p_bold_start('Conclusions: ',
    'Routine clinicopathological variables impose an information ceiling that prevents '
    'reliable reproduction of 4-class PAM50 subtypes. The irreducible uncertainty '
    'concentrates at the Luminal A/Luminal B boundary, defining a clinically relevant '
    'grey zone in which molecular testing adds the greatest value.')

# ============================================================
# 1. INTRODUCTION
# ============================================================
pdf.h1('1. Introduction')

pdf.p(
    'Breast cancer is a biologically heterogeneous disease. Gene-expression profiling '
    'established the major intrinsic subtypes -- Luminal A, Luminal B, HER2-enriched, and '
    'Basal-like -- which differ in prognosis, proliferation, endocrine sensitivity, and '
    'treatment responsiveness [1,2]. Among available molecular classifiers, PAM50 remains '
    'the most widely adopted framework for intrinsic subtyping and is deeply embedded in '
    'translational research and clinical decision-making [3].')

pdf.p(
    'In routine practice, however, true molecular subtyping is often unavailable. Most '
    'centres instead rely on immunohistochemical surrogates based on ER, PR, HER2, and '
    'Ki-67, as popularised by the St Gallen consensus [4]. This approach is pragmatic, '
    'inexpensive, and globally scalable, but it is only an approximation of intrinsic '
    'biology. Discordance between immunohistochemical surrogates and PAM50 is well '
    'recognised, particularly in hormone receptor-positive disease, where the Luminal '
    'A/Luminal B distinction reflects a continuous proliferative axis that routine markers '
    'capture only imperfectly [5,6].')

pdf.p(
    'An intuitive next question is whether machine-learning methods can recover additional '
    'molecular information from the same routine variables and improve on the rule-based '
    'surrogate. If successful, a purely computational approach could refine subtype '
    'approximation without additional laboratory cost. If unsuccessful, the negative result '
    'is still clinically meaningful: it would indicate that routine pathology data contain '
    'an information ceiling that no algorithm can overcome, and that molecular testing '
    'remains irreplaceable in specific patient subgroups.')

pdf.p(
    'We therefore asked two linked questions. First, how accurately does the conventional '
    'immunohistochemical surrogate reproduce 4-class PAM50 intrinsic subtypes across '
    'multiple independent cohorts? Second, can machine-learning models built from the same '
    'routine clinicopathological variables improve on that approximation? Our aim was not '
    'to replace PAM50, but to define the practical limit of routine-data recoverability '
    'and identify the subtype boundary at which molecular testing provides the greatest '
    'incremental value.')

# ============================================================
# 2. MATERIALS AND METHODS
# ============================================================
pdf.h1('2. Materials and methods')

pdf.h2('2.1 Study design')
pdf.p(
    'This was a retrospective, purely in silico, multicohort diagnostic-accuracy study. '
    'The index tests were the conventional immunohistochemical surrogate and each '
    'machine-learning classifier. The reference standard was the published 4-class PAM50 '
    'label in each cohort. No new biological samples were generated or analysed. The study '
    'was designed and reported according to TRIPOD principles for multivariable prediction '
    'model studies [7].')

pdf.h2('2.2 Data sources and cohorts')
pdf.p('Four public breast cancer datasets were analysed (Table 1, Fig. 1).')
pdf.p(
    'Development cohorts: GSE81538 (SCAN-B; source n=405, analysable 4-class subset n=383) '
    'comprised RNA-seq data with multi-observer pathology consensus for ER, PR, HER2, Ki-67, '
    'and Nottingham histological grade (NHG) [8]. GSE96058 (SCAN-B; source n=3,069, '
    'analysable 4-class subset n=2,867) comprised RNA-seq data with binary '
    'immunohistochemical status and NHG grade [8].')
pdf.p(
    'External validation cohorts: TCGA-BRCA (clinical source n=1,108, analysable 4-class '
    'subset n=519) included RNA-seq data and routine ER, PR, and HER2 assessment, with '
    'HER2-equivocal cases resolved by FISH when available; histological grade was '
    'unavailable [9]. METABRIC (clinical source n=2,509, analysable 4-class subset n=1,608) '
    'included microarray-based expression data and routine ER, PR, HER2, and NHG grade [10].')
pdf.p(
    'Normal-like and claudin-low labels were excluded to ensure a uniform 4-class endpoint '
    'across cohorts. Publicly available processed data were obtained from NCBI GEO and '
    'cBioPortal.')

# TABLE 1
pdf.small_table(t_flow,
    'Table 1. Cohort characteristics and evaluable sample sizes by feature set.')

pdf.h2('2.3 Variable harmonisation')
pdf.p(
    'ER and PR were coded as binary positive/negative variables across all cohorts. HER2 '
    'was harmonised as binary positive/negative; equivocal cases were resolved using in situ '
    'hybridisation when available. Ki-67 was available as a continuous percentage in GSE81538 '
    'and as a binary high/low variable in GSE96058; it was unavailable in TCGA-BRCA and '
    'METABRIC. Histological grade (NHG 1-3) was available in GSE81538, GSE96058, and '
    'METABRIC, but not in TCGA-BRCA. Because variable granularity differed across cohorts, '
    'analyses were organised into prespecified feature sets rather than forcing a single '
    'complete-case dataset across all platforms.')

pdf.h2('2.4 Conventional surrogate classification')
pdf.p(
    'The baseline comparator was a St Gallen-like immunohistochemical surrogate [4]. '
    'Luminal A-like was defined as HR-positive/HER2-negative with low proliferation; '
    'Luminal B-like as HR-positive/HER2-negative with high proliferation or '
    'HR-positive/HER2-positive; HER2-positive non-luminal as HR-negative/HER2-positive; '
    'and triple-negative as HR-negative/HER2-negative. Proliferation was defined as '
    'Ki-67 >=20% when available, or grade 3 when Ki-67 was not available. Cases missing '
    'ER, PR, or HER2 were excluded from surrogate classification.')

pdf.h2('2.5 Feature sets')
pdf.p(
    'Three nested feature sets were evaluated to reflect increasing real-world data '
    'availability: Set 1 (core IHC): ER, PR, HER2. Set 2 (IHC + grade): Set 1 plus '
    'histological grade. Set 3 (IHC + grade + Ki-67): Set 2 plus Ki-67. Set 3 was not '
    'available in external validation cohorts because Ki-67 was absent or not sufficiently '
    'granular in TCGA-BRCA and METABRIC.')

pdf.h2('2.6 Machine-learning models')
pdf.p(
    'Three supervised multiclass classifiers were trained on the combined GSE81538 and '
    'GSE96058 development cohorts: multinomial logistic regression with balanced class '
    'weights, random forest (500 trees), and XGBoost (500 rounds, maximum depth 6, '
    'learning rate 0.1). Hyperparameters were fixed before external validation. No '
    'optimisation was performed on validation cohorts.')

pdf.h2('2.7 Outcomes and statistical analysis')
pdf.p(
    'The primary endpoint was macro-averaged F1-score for 4-class PAM50 prediction. '
    'Secondary metrics were Cohen\'s kappa and balanced accuracy. All performance estimates '
    'are reported with bootstrap 95% confidence intervals derived from 1,000 stratified '
    'resamples. Head-to-head comparisons between machine-learning models and the '
    'immunohistochemical surrogate were restricted to the exact intersection of cases '
    'classifiable by both methods, ensuring identical denominators.')
pdf.p(
    'Prespecified sensitivity analyses included: (1) a 3-class formulation in which '
    'Luminal A and Luminal B were collapsed into a single luminal class; and (2) a '
    'grey-zone analysis based on the maximum predicted class probability, using low '
    '(<0.50), intermediate (0.50-0.70), and high (>0.70) confidence bins.')

# ============================================================
# 3. RESULTS
# ============================================================
pdf.h1('3. Results')

pdf.h2('3.1 Cohort characteristics')
pdf.p(
    'After exclusions, 5,377 tumours with 4-class PAM50 labels were included: 3,250 in '
    'the development cohorts and 2,127 in external validation cohorts. Luminal A was the '
    'most prevalent subtype in every cohort, followed by Luminal B, with smaller '
    'HER2-enriched and Basal-like fractions. ER positivity ranged from 77% to 92%, and '
    'HER2 positivity from 13% to 22%. Histological grade distributions were broadly '
    'comparable across the three cohorts in which grade was available (Fig. 1). These '
    'between-cohort differences created a realistic and deliberately stringent validation '
    'setting spanning two molecular platforms and heterogeneous biomarker availability.')

# FIGURE 1 -- Cohort characteristics (R)
pdf.fig(os.path.join(FIG_R, 'fig2_cohort_characteristics.png'),
    'Fig. 1. Cohort characteristics. (A) PAM50 subtype distribution by cohort. '
    '(B) ER and HER2 positivity rates. (C) Histological grade distribution. '
    '(D) Absolute counts by subtype.',
    w=170)

pdf.h2('3.2 Baseline performance of the immunohistochemical surrogate')
pdf.p(
    'The immunohistochemical surrogate was classifiable in 4,694 of 5,377 tumours (87.3%). '
    'In METABRIC head-to-head analysis (n=1,554), it achieved macro-F1 0.646 (95% CI '
    '0.623-0.669) and kappa 0.471 (0.436-0.506). Concordance was highest for Basal-like '
    'and HER2-enriched tumours and clearly lower for luminal disease.')
pdf.p(
    'The dominant error pattern was crossover at the Luminal A/Luminal B boundary. In '
    'METABRIC, 42.5% of molecular Luminal B tumours received a Luminal A-like surrogate '
    'label, while 26.9% of molecular Luminal A tumours were overcalled as Luminal B-like '
    '(Fig. 2, Table 2). The same general pattern was observed across all cohorts, although '
    'TCGA-BRCA showed an unstable extreme due to small evaluable luminal subsets and the '
    'absence of grade.')

# FIGURE 2 -- Luminal crossover (R)
pdf.fig(os.path.join(FIG_R, 'fig4_luminal_crossover.png'),
    'Fig. 2. Luminal A/B crossover by IHC surrogate across cohorts. The Luminal '
    'B-to-Luminal A misclassification is the dominant error in METABRIC (42.5%), while '
    'Luminal A-to-Luminal B misclassification predominates in TCGA-BRCA (92.9%, n=28).',
    w=155)

# TABLE 2
pdf.small_table(t_lumab,
    'Table 2. Luminal A/Luminal B crossover rates by cohort.')

pdf.h2('3.3 Machine-learning models did not outperform the surrogate')
pdf.p(
    'No machine-learning model outperformed the immunohistochemical surrogate in any '
    'external head-to-head comparison (Fig. 3).')
pdf.p(
    'In METABRIC, the best Set 1 model (XGBoost) achieved macro-F1 0.523 (95% CI '
    '0.503-0.544), substantially below the surrogate. Adding grade improved performance '
    'modestly: the best Set 2 model (XGBoost) reached 0.559 (0.533-0.584), but still '
    'remained inferior to the surrogate value of 0.644-0.646 depending on the matched '
    'subset.')
pdf.p(
    'In TCGA-BRCA, the surrogate achieved macro-F1 0.485 (0.431-0.541) in the head-to-head '
    'subset (n=162), whereas the best machine-learning model reached 0.368. Across both '
    'external cohorts, the pattern was consistent: grade added some recoverable signal, but '
    'the gain was insufficient to match the conventional surrogate.')

# FIGURE 3 -- Forest plot (R)
pdf.fig(os.path.join(FIG_R, 'fig3_forest_h2h.png'),
    'Fig. 3. Head-to-head macro-F1 comparison with bootstrap 95% confidence intervals. '
    'Red: IHC surrogate. Blue: ML models. Comparisons on identical evaluable subsets show '
    'the surrogate consistently outperforms all ML classifiers.',
    w=160)

pdf.h2('3.4 Confusion-matrix analysis')
pdf.p(
    'Normalised confusion matrices in METABRIC (Fig. 4) showed that both approaches '
    'captured broad non-luminal biology better than fine luminal subclassification. The '
    'surrogate identified Basal-like and HER2-enriched tumours with relatively high '
    'sensitivity, but remained poor at separating Luminal A from Luminal B. XGBoost with '
    'grade modestly improved Luminal B capture at the cost of reduced Luminal A specificity, '
    'indicating a trade-off rather than a net increase in recoverable information.')

# FIGURE 4 -- Confusion matrices (Python -- heatmaps)
pdf.fig(os.path.join(FIG_DIR, 'fig4_confusion.png'),
    'Fig. 4. Normalised confusion matrices on METABRIC. (A) IHC surrogate. (B) XGBoost '
    'Set 1 (ER, PR, HER2). (C) XGBoost Set 2 (+ grade). Row-normalised proportions; '
    'darker cells indicate higher concordance.',
    w=170)

pdf.h2('3.5 Grey-zone analysis')
pdf.p(
    'Prediction confidence revealed a clinically meaningful low-certainty subgroup. In '
    'METABRIC, 13.5% of cases (n=208) had a maximum class probability <0.50. These tumours '
    'were predominantly luminal (73.6%) and showed only 15.9% machine-learning accuracy, '
    'while the surrogate still reached 54.8% accuracy (Fig. 5, Table 3).')
pdf.p(
    'By contrast, in the high-confidence zone (>0.70; 58.2% of cases), machine learning '
    'and the surrogate performed similarly (73.1% versus 73.8%). The grey-zone framework '
    'therefore identifies a specific subgroup -- predominantly HR-positive/HER2-negative '
    'disease -- in which routine-data-based approximation is least reliable and molecular '
    'testing is most likely to add value.')

# FIGURE 5 -- Grey zone (R)
pdf.fig(os.path.join(FIG_R, 'fig5_grey_zone.png'),
    'Fig. 5. Grey-zone analysis on METABRIC. (A) Accuracy by confidence zone for ML '
    'and IHC surrogate. (B) Distribution of cases across confidence tiers. (C) Luminal '
    'A + B proportion within each confidence zone.',
    w=160)

# TABLE 3
pdf.small_table(t_gz,
    'Table 3. Grey-zone analysis by confidence tier.')

pdf.h2('3.6 Sensitivity analysis: 3-class collapse')
pdf.p(
    'Collapsing Luminal A and Luminal B into a single luminal class substantially improved '
    'performance. Macro-F1 increased from 0.514 to 0.777 in TCGA-BRCA and from 0.522 to '
    '0.767 in METABRIC (Table 4). This result is central to interpretation: most of the '
    'classification deficit resides within the luminal boundary rather than in the broader '
    'separation of luminal, HER2-enriched, and Basal-like disease.')

# TABLE 4
pdf.small_table(t_sens,
    'Table 4. Sensitivity analysis: 4-class versus 3-class performance.')

pdf.h2('3.7 Information ceiling')
pdf.p(
    'Taken together, the results indicate an information ceiling imposed by routine '
    'clinicopathological variables (Fig. 6). Adding grade and, where available, Ki-67 '
    'produced incremental gains, but these gains plateaued below the surrogate and well '
    'below molecular classification. The limiting factor was therefore not model choice, '
    'but information content in the inputs.')

# FIGURE 6 -- Information ceiling (R)
pdf.fig(os.path.join(FIG_R, 'fig10_information_ceiling.png'),
    'Fig. 6. The information ceiling concept. ML performance improves with feature '
    'complexity but plateaus below the IHC surrogate (dotted line). Only gene-expression '
    'profiling (PAM50, 50 genes) breaks through the ceiling. The shaded zone indicates '
    'the information ceiling imposed by routine clinicopathological variables.',
    w=140)

# ============================================================
# 4. DISCUSSION
# ============================================================
pdf.h1('4. Discussion')

pdf.p(
    'This multicohort in silico study shows that routine pathology variables do not '
    'contain enough stable information to reliably reproduce 4-class PAM50 intrinsic '
    'subtypes across independent cohorts. Three findings define this conclusion: the '
    'conventional immunohistochemical surrogate misclassified approximately one-third of '
    'tumours; most errors concentrated at the Luminal A/Luminal B boundary; and '
    'machine-learning models did not consistently improve on the surrogate in external '
    'validation.')

pdf.p(
    'The negative result is therefore the main result. Machine learning did not fail '
    'because the algorithms were intrinsically inadequate; rather, the routine variables '
    'themselves appear insufficiently informative for stable 4-class reconstruction of '
    'intrinsic biology. This distinction matters. It shifts the interpretation away from '
    'model optimisation and toward the practical limit of what routine pathology can encode.')

pdf.p(
    'The luminal boundary was the key bottleneck. Biologically, the distinction between '
    'Luminal A and Luminal B reflects a continuous proliferative gradient driven by '
    'coordinated gene-expression programs [1]. In contrast, routine pathology compresses '
    'this axis into much coarser markers such as Ki-67 and histological grade. Even when '
    'both variables were available, the gap was narrowed only modestly. The sensitivity '
    'analysis supports this interpretation: once Luminal A and Luminal B were collapsed, '
    'performance rose sharply in both validation cohorts, indicating that broad luminal '
    'versus non-luminal separation is recoverable, while fine luminal subclassification '
    'is not.')

pdf.p(
    'This finding has direct clinical implications. The practical value of molecular '
    'subtyping is unlikely to be uniform across all patients. Tumours with clearly '
    'non-luminal phenotypes, especially triple-negative and HER2-driven disease, are '
    'already reasonably well captured by routine biomarkers. By contrast, hormone '
    'receptor-positive/HER2-negative tumours near the Luminal A/Luminal B boundary '
    'remain the true zone of irreducible uncertainty [11]. In this context, the grey-zone '
    'analysis is useful not because it produces a better classifier, but because it helps '
    'identify where routine methods are least trustworthy and where molecular testing is '
    'most likely to alter biological interpretation.')

pdf.p(
    'Our study also offers a broader methodological lesson. Algorithmic complexity cannot '
    'fully compensate for information-poor inputs. In this setting, the difference between '
    'logistic regression, random forest, and XGBoost was less important than the limited '
    'granularity of ER, PR, HER2, grade, and Ki-67 across public cohorts. This suggests '
    'that future efforts should focus less on increasingly complex classifiers built on the '
    'same routine variables and more on identifying what additional information -- continuous '
    'biomarker measures, digital pathology, morphology-derived features, or true molecular '
    'data -- is required to break the ceiling.')

pdf.h2('4.1 Relation to prior work')
pdf.p(
    'Prior studies have shown incomplete concordance between immunohistochemical surrogates '
    'and PAM50, particularly in luminal disease [5,6,12]. Our results are aligned with that '
    'literature, but extend it in three ways: first, by testing multiple machine-learning '
    'approaches rather than only rule-based surrogates; second, by requiring strict external '
    'validation across independent cohorts and platforms; and third, by using head-to-head '
    'comparisons on identical evaluable subsets. These design choices make the negative '
    'result more rigorous and, in our view, more clinically informative.')

pdf.h2('4.2 Strengths and limitations')
pdf.p(
    'Strengths include the use of four independent cohorts spanning two molecular platforms, '
    'strict external validation, matched-denominator comparisons between the surrogate and '
    'machine-learning models, bootstrap confidence intervals for all core metrics, and a '
    'grey-zone framework that translates prediction uncertainty into potential clinical '
    'utility.')
pdf.p(
    'The study also has limitations. First, most routine biomarkers were available only in '
    'simplified categorical format, especially ER, PR, and HER2, likely underestimating the '
    'potential contribution of more granular pathology data. Second, continuous Ki-67 was '
    'available only in the smaller SCAN-B cohort, and histological grade was absent in '
    'TCGA-BRCA, limiting portability of enriched feature sets. Third, PAM50 labels were '
    'obtained from public resources with cohort-specific implementations. Fourth, this was '
    'a purely in silico study without outcome-based confirmation of the clinical '
    'consequences of discordant luminal assignments.')
pdf.p(
    'These limitations do not weaken the core conclusion. If anything, they reflect the '
    'conditions under which routine surrogate subtyping is commonly used in practice.')

# ============================================================
# 5. CONCLUSIONS
# ============================================================
pdf.h1('5. Conclusions')

pdf.p(
    'Routine clinicopathological variables impose an information ceiling that prevents '
    'reliable reproduction of 4-class PAM50 intrinsic subtypes. Machine-learning models '
    'do not overcome this limitation because the main constraint lies in the input data, '
    'not in the classifier. The irreducible uncertainty concentrates at the Luminal '
    'A/Luminal B boundary, defining a clinically relevant grey zone in which molecular '
    'testing is most likely to add value. These findings support a selective, rather than '
    'indiscriminate, use of molecular subtyping in breast cancer.')

# ============================================================
# FUNDING
# ============================================================
pdf.h1('Funding')
pdf.p('This research did not receive any specific grant from funding agencies in the '
      'public, commercial, or not-for-profit sectors.')

# ============================================================
# DECLARATION OF COMPETING INTEREST
# ============================================================
pdf.h1('Declaration of competing interest')
pdf.p('The authors declare that they have no known competing financial interests or '
      'personal relationships that could have appeared to influence the work reported '
      'in this paper.')

# ============================================================
# CRediT
# ============================================================
pdf.h1('CRediT authorship contribution statement')
pdf.p(
    'Rafael de Negreiros Botan: Conceptualisation, Methodology, Software, Formal analysis, '
    'Data curation, Writing -- original draft, Visualisation. '
    'Joao Batista de Sousa: Supervision, Writing -- review & editing.')

# ============================================================
# AI DECLARATION
# ============================================================
pdf.h1('Declaration of generative AI in manuscript preparation')
pdf.p(
    'During the preparation of this work, the authors used generative AI tools to support '
    'language editing, structural refinement, and stylistic revision of the manuscript. '
    'After using these tools, the authors reviewed and edited the content as needed and '
    'take full responsibility for the content of the published article.')

# ============================================================
# DATA AVAILABILITY
# ============================================================
pdf.h1('Data availability')
pdf.p(
    'All data used in this study are publicly available. GSE81538 and GSE96058 are '
    'available through NCBI GEO; TCGA-BRCA and METABRIC clinical data were accessed '
    'through cBioPortal. Analysis code is available from the corresponding author upon '
    'reasonable request.')

# ============================================================
# REFERENCES
# ============================================================
pdf.h1('References')
pdf.set_font('Helvetica', '', 7.5)
refs = [
    '[1] Parker JS, Mullins M, Cheang MC, et al. Supervised risk predictor of breast cancer based on intrinsic subtypes. J Clin Oncol 2009;27(8):1160-7.',
    '[2] Perou CM, Sorlie T, Eisen MB, et al. Molecular portraits of human breast tumours. Nature 2000;406(6797):747-52.',
    '[3] Prat A, Fan C, Fernandez A, et al. Clinical implications of the intrinsic molecular subtypes of breast cancer. Breast 2015;24(Suppl 2):S26-35.',
    '[4] Goldhirsch A, Winer EP, Coates AS, et al. Personalizing the treatment of women with early breast cancer: highlights of the St Gallen International Expert Consensus 2013. Ann Oncol 2013;24(9):2206-23.',
    '[5] Bastien RR, Rodriguez-Lescure A, Ebbert MT, et al. PAM50 breast cancer subtyping by RT-qPCR and concordance with standard clinical molecular markers. BMC Med Genomics 2012;5:44.',
    '[6] Prat A, Cheang MC, Martin M, et al. Prognostic significance of progesterone receptor-positive tumor cells within immunohistochemically defined luminal A breast cancer. J Clin Oncol 2013;31(2):203-9.',
    '[7] Collins GS, Reitsma JB, Altman DG, Moons KG. Transparent reporting of a multivariable prediction model for individual prognosis or diagnosis (TRIPOD). BMJ 2015;350:g7594.',
    '[8] Brueffer C, Vallon-Christersson J, Grabau D, et al. Clinical value of RNA sequencing-based classifiers for prediction of the five conventional breast cancer biomarkers: a SCAN-B report. JCO Precis Oncol 2018;2:1-18.',
    '[9] Cancer Genome Atlas Network. Comprehensive molecular portraits of human breast tumours. Nature 2012;490(7418):61-70.',
    '[10] Curtis C, Shah SP, Chin SF, et al. The genomic and transcriptomic architecture of 2,000 breast tumours reveals novel subgroups. Nature 2012;486(7403):346-52.',
    '[11] Cardoso F, van\'t Veer LJ, Bogaerts J, et al. 70-gene signature as an aid to treatment decisions in early-stage breast cancer. N Engl J Med 2016;375(8):717-29.',
    '[12] Chia SK, Bramwell VH, Tu D, et al. A 50-gene intrinsic subtype classifier for prognosis and prediction of benefit from adjuvant tamoxifen. Clin Cancer Res 2012;18(16):4465-72.',
]
for ref in refs:
    pdf.multi_cell(0, 3.5, ref)
    pdf.ln(0.8)

# ============================================================
# SUPPLEMENTARY FIGURES
# ============================================================
pdf.add_page()
pdf.h1('Supplementary Material')

pdf.fig(os.path.join(FIG_R, 'fig7_sensitivity_3v4.png'),
    'Supplementary Fig. S1. Sensitivity analysis: 4-class vs. 3-class (luminal grouped) '
    'performance with bootstrap 95% CIs.',
    w=130)

pdf.fig(os.path.join(FIG_R, 'fig8_feature_set_comparison.png'),
    'Supplementary Fig. S2. ML performance by feature set on METABRIC. Adding grade '
    '(Set 2) improves all ML models but none reaches the IHC surrogate (dashed red line).',
    w=150)

pdf.fig(os.path.join(FIG_R, 'fig9_multimetric_panel.png'),
    'Supplementary Fig. S3. Multi-metric comparison on METABRIC (head-to-head). The IHC '
    'surrogate outperforms ML on every metric: macro-F1, kappa, and balanced accuracy.',
    w=150)

pdf.fig(os.path.join(FIG_R, 'fig6_feature_importance.png'),
    'Supplementary Fig. S4. XGBoost feature importance (gain). ER status dominates; '
    'proliferation markers (Ki-67, grade) contribute modestly.',
    w=120)

# ============================================================
# SAVE
# ============================================================
pdf_path = os.path.join(MS_DIR, "manuscript_TheBreast_FINAL.pdf")
pdf.output(pdf_path)
print(f"Manuscript saved: {pdf_path}")
print(f"Size: {os.path.getsize(pdf_path)/1024:.0f} KB, Pages: {pdf.page_no()}")
