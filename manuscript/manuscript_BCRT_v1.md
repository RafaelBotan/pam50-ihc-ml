# Routine clinicopathological data cannot reliably reproduce 4-class PAM50 intrinsic subtypes in breast cancer: a multicohort in silico study defining the luminal grey zone

**Authors:** Rafael de Negreiros Botan¹,*, Sandro José Martins³, João Batista de Sousa¹,²

¹ University of Brasília, Brasília, Brazil, Medical Sciences Postgraduate Program, School of Medicine, DF, Brazil
² University of Brasília, Brasília, Brazil, Department of Colorectal Surgery, Hospital Universitário de Brasília, Brasília, Brazil
³ University of Brasília, Brasília, Brazil, Department of Oncology, Hospital Universitário de Brasília, Brasília, Brazil

Corresponding author: Rafael de Negreiros Botan — oncologista@gmail.com

**Running title:** Information ceiling for routine-data approximation of PAM50

**Keywords:** breast cancer; PAM50; intrinsic subtype; immunohistochemistry; machine learning; grey zone

---

## Abstract

**Purpose:** Immunohistochemistry-based surrogates approximate intrinsic breast cancer subtypes in routine care, but agreement with PAM50 is incomplete. We tested whether machine-learning models using routine clinicopathological variables could improve on the conventional surrogate and quantified the resulting information ceiling.

**Methods:** Four public datasets with 4-class PAM50 labels were analysed (GSE81538, n=383; GSE96058, n=2,867; TCGA-BRCA, n=519; METABRIC, n=1,608; total n=5,377). Multinomial logistic regression, random forest, and XGBoost were trained on SCAN-B using three nested pathology feature sets: receptor-only (ER/PR/HER2), receptor-grade (+grade), and full pathology (+Ki-67). External validation was performed in TCGA-BRCA and METABRIC. Head-to-head comparisons with the surrogate used identical evaluable subsets and bootstrap 95% confidence intervals.

**Results:** No model outperformed the surrogate externally. In the METABRIC receptor-grade matched subset (n=1,544), surrogate macro-F1 was 0.644 (95% CI 0.616-0.669) versus 0.559 (0.533-0.584) for the best model, XGBoost with grade. The dominant error was Luminal A/Luminal B crossover: 42.5% of molecular Luminal B tumours received a Luminal A-like surrogate label. Collapsing luminal classes increased macro-F1 to 0.767 in METABRIC. A low model-confidence grey zone comprised 13.5% of cases, was 73.6% luminal, and showed 15.9% machine-learning accuracy.

**Conclusion:** Routine clinicopathological variables impose an information ceiling that prevents reliable 4-class PAM50 reproduction. Uncertainty concentrates at the Luminal A/Luminal B boundary, defining a clinically relevant grey zone where molecular testing is most likely to clarify intrinsic subtype assignment.

---

## 1. Introduction

Breast cancer is a biologically heterogeneous disease. Gene-expression profiling established the major intrinsic subtypes—Luminal A, Luminal B, HER2-enriched, and Basal-like—which differ in prognosis, proliferation, endocrine sensitivity, and treatment responsiveness [1,2]. Among available molecular classifiers, PAM50 remains the most widely adopted framework for intrinsic subtyping and is deeply embedded in translational research and clinical decision-making [3].

In routine practice, however, true molecular subtyping is often unavailable. Most centres instead rely on immunohistochemical surrogates based on ER, PR, HER2, and Ki-67, as popularised by the St Gallen consensus [4]. This approach is pragmatic, inexpensive, and globally scalable, but it is only an approximation of intrinsic biology. Discordance between immunohistochemical surrogates and PAM50 is well recognised, particularly in hormone receptor-positive disease, where the Luminal A/Luminal B distinction reflects a continuous proliferative axis that routine markers capture only imperfectly [5,6].

An intuitive next question is whether machine-learning methods can recover additional molecular information from the same routine variables and improve on the rule-based surrogate. If successful, a purely computational approach could refine subtype approximation without additional laboratory cost. If unsuccessful, the negative result would still be clinically meaningful: it would indicate that routine clinicopathological data contain an information ceiling that no routine-data algorithm is likely to overcome, and that molecular testing remains irreplaceable in specific patient subgroups. If routine variables cannot recover the missing information, compact expression-based assays may represent a more rational escalation strategy for biologically ambiguous cases.

We therefore asked two linked questions. First, how accurately does the conventional immunohistochemical surrogate reproduce 4-class PAM50 intrinsic subtypes across multiple independent cohorts? Second, can machine-learning models built from the same routine clinicopathological variables improve on that approximation? Our aim was not to replace PAM50, but to define the practical limit of routine-data recoverability and identify the subtype boundary at which molecular testing provides the greatest incremental value.

## 2. Materials and methods

### 2.1 Study design

This was a retrospective, purely in silico, multicohort diagnostic-accuracy study. The index tests were the conventional immunohistochemical surrogate and each machine-learning classifier. The reference standard was the published 4-class PAM50 label in each cohort. No new biological samples were generated or analysed. The study was designed and reported according to TRIPOD principles for multivariable prediction model studies, with consideration of TRIPOD+AI extensions for machine-learning models and STARD principles for diagnostic-accuracy reporting [7-9].

### 2.2 Data sources and cohorts

Four public breast cancer datasets were analysed (Table 1, Fig. 1).

**Development cohorts:** GSE81538 (SCAN-B; source n=405, analysable 4-class subset n=383) comprised RNA-seq data with multi-observer pathology consensus for ER, PR, HER2, Ki-67, and Nottingham histological grade (NHG) [10]. GSE96058 (SCAN-B; source n=3,069, analysable 4-class subset n=2,867) comprised RNA-seq data with binary immunohistochemical status and NHG grade [10].

**External validation cohorts:** TCGA-BRCA (clinical source n=1,108, analysable 4-class subset n=519) included RNA-seq data and routine ER, PR, and HER2 assessment, with HER2-equivocal cases resolved by FISH when available; histological grade was unavailable [11]. METABRIC (clinical source n=2,509, analysable 4-class subset n=1,608) included microarray-based expression data and routine ER, PR, HER2, and NHG grade [12].

Normal-like and claudin-low labels were excluded to ensure a uniform 4-class endpoint across cohorts. Publicly available processed data were obtained from NCBI GEO and cBioPortal.

**Table 1.** Cohort characteristics and evaluable sample sizes by pathology feature set and surrogate applicability.

*Abbreviations:* PAM50, Prediction Analysis of Microarray 50; IHC, immunohistochemistry. Receptor-only (Set 1): ER, PR, and HER2. Receptor-grade (Set 2): receptor-only variables plus histological grade. Full pathology (Set 3): receptor-grade variables plus Ki-67. N (4-class PAM50) refers to tumours with an evaluable 4-class molecular reference label after exclusion of Normal-like and claudin-low categories. N (Surrogate classifiable) refers to tumours for which full 4-class surrogate assignment was possible. The surrogate used derived hormone receptor status: HR-positive was assigned when either ER or PR was positive, whereas HR-negative required both ER and PR to be negative; therefore, surrogate classifiability can exceed receptor-only model completeness when one hormone receptor was missing but the other was positive. In HR-positive/HER2-negative tumours, surrogate assignment also required a proliferation variable (Ki-67 or grade) to separate Luminal A-like from Luminal B-like; therefore, surrogate applicability was reduced in TCGA-BRCA, where grade was unavailable and Ki-67 was absent. The head-to-head columns refer to exact matched subsets classifiable by both the specified machine-learning feature set and the surrogate.

### 2.3 Variable harmonisation

ER and PR were coded as binary positive/negative variables across all cohorts. HER2 was harmonised as binary positive/negative; equivocal cases were resolved using in situ hybridisation when available. Ki-67 was available as a continuous percentage in GSE81538 and as a binary high/low variable in GSE96058; it was unavailable in TCGA-BRCA and METABRIC. For full-pathology modelling, continuous Ki-67 values in GSE81538 were retained, and binary Ki-67 high/low values in GSE96058 were encoded on an approximate percentage scale as 30% and 10%, respectively. This approximate monotonic encoding was used only for supportive full-pathology development analyses; no external validation result depended on Ki-67 because Ki-67 was unavailable in TCGA-BRCA and METABRIC. Histological grade (NHG 1-3) was available in GSE81538, GSE96058, and METABRIC, but not in TCGA-BRCA. Because variable granularity differed across cohorts, analyses were organised into prespecified feature sets rather than forcing a single complete-case dataset across all platforms.

This heterogeneity affected not only model portability but also the feasibility of rule-based 4-class surrogate assignment, particularly in HR-positive/HER2-negative tumours requiring a proliferation variable for luminal subclassification.

### 2.4 Conventional surrogate classification

The baseline comparator was a St Gallen-like immunohistochemical surrogate. Tumours were classified as Luminal A-like, Luminal B-like, HER2-positive non-luminal, or triple-negative according to hormone receptor status, HER2 status, and proliferation information.

Operationally, HR-positive was assigned when either ER or PR was positive, whereas HR-negative required both ER and PR to be negative. Luminal A-like was defined as HR-positive/HER2-negative with low proliferation; Luminal B-like as HR-positive/HER2-negative with high proliferation or HR-positive/HER2-positive; HER2-positive non-luminal as HR-negative/HER2-positive; and triple-negative as HR-negative/HER2-negative. Because PR percentage and continuous Ki-67 were not uniformly available across cohorts, the surrogate was operationalised using a pragmatic St Gallen-like rule based on HR status, HER2 status, Ki-67 when available, and grade as a proliferation fallback when Ki-67 was unavailable. Proliferation was defined as Ki-67 ≥20% when available, or grade 3 when Ki-67 was unavailable but grade was present. When both Ki-67 and grade were available, Ki-67 was prioritised for surrogate luminal subclassification, with grade used only as a fallback when Ki-67 was unavailable.

Importantly, full 4-class surrogate assignment required a proliferation variable for HR-positive/HER2-negative tumours. Therefore, in cohorts lacking both Ki-67 and grade, HR-positive/HER2-negative cases could not be further subdivided into Luminal A-like versus Luminal B-like and were considered non-classifiable for surrogate-based 4-class assignment. This explains the lower number of surrogate-classifiable cases in TCGA-BRCA despite broader availability of receptor-only variables.

Cases without sufficient hormone receptor information to assign HR-positive or HR-negative status, or without HER2 status, were excluded from surrogate classification.

### 2.5 Pathology feature sets

Three nested pathology feature sets were evaluated to reflect increasing real-world data availability. The receptor-only set (Set 1) included ER, PR, and HER2. The receptor-grade set (Set 2) added histological grade. The full-pathology set (Set 3) added Ki-67 to receptor-grade variables. Full pathology was not available in external validation cohorts because Ki-67 was absent or not sufficiently granular in TCGA-BRCA and METABRIC.

### 2.6 Machine-learning models

Three supervised multiclass classifiers were trained on the combined GSE81538 and GSE96058 development cohorts: multinomial logistic regression, random forest, and XGBoost [13,14]. Analyses were implemented in Python 3.13.13 using pandas 2.2.3, NumPy 2.4.2, scikit-learn 1.8.0, and XGBoost 3.2.0, with fixed random seed 42. Model training used complete cases for each prespecified feature set; no validation-cohort imputation or outcome-informed preprocessing was performed. Binary predictors were coded as 0/1 and grade as an ordinal 1-3 variable. Multinomial logistic regression used the lbfgs solver, C=1.0, maximum 2000 iterations, balanced class weights, and z-standardised predictors. Random forest used 500 trees, balanced class weights, and raw coded predictors. XGBoost used a multiclass soft-probability objective, 500 boosting rounds, maximum depth 6, learning rate 0.1, and raw coded predictors. Hyperparameters were fixed before external validation, and all unspecified model hyperparameters were left at package defaults. No optimisation was performed on validation cohorts. No overlapping sample identifiers were present between the two SCAN-B development cohorts in the harmonised dataset.

### 2.7 Outcomes and statistical analysis

The primary endpoint was macro-averaged F1-score for 4-class PAM50 prediction. Cohen's kappa was a secondary metric. Macro-F1 and kappa estimates are reported with bootstrap 95% confidence intervals derived from 1,000 stratified resamples. Head-to-head comparisons between machine-learning models and the immunohistochemical surrogate were restricted to the exact intersection of cases classifiable by both methods, ensuring identical denominators. Paired macro-F1 differences were estimated by bootstrap resampling the same matched cases.

Prespecified sensitivity analyses included: (1) a 3-class formulation in which Luminal A and Luminal B were collapsed into a single luminal class; and (2) a grey-zone analysis based on the maximum predicted class probability from XGBoost receptor-grade, using low (<0.50), intermediate (0.50-0.70), and high (>0.70) model-confidence bins. No probability calibration was performed; these values were interpreted as relative model-confidence scores, not calibrated clinical risks.

Separate descriptive analyses performed on full model-evaluable subsets are presented only as supportive analyses and should not be interpreted as direct comparisons with the surrogate unless explicitly labelled as matched head-to-head.

## 3. Results

### 3.1 Cohort characteristics

After exclusions, 5,377 tumours with 4-class PAM50 labels were included: 3,250 in the development cohorts and 2,127 in external validation cohorts. Luminal A was the most prevalent subtype in every cohort, followed by Luminal B, with smaller HER2-enriched and Basal-like fractions. ER positivity ranged from 76% to 86%, and HER2 positivity from 13% to 22%. Histological grade distributions were broadly comparable across the three cohorts in which grade was available (Fig. 1). These between-cohort differences created a realistic and deliberately stringent validation setting spanning two molecular platforms and heterogeneous biomarker availability.

**Fig. 1.** Cohort characteristics. (A) PAM50 subtype distribution by cohort. (B) ER and HER2 positivity rates. (C) Histological grade distribution; grade was unavailable for TCGA-BRCA in the harmonised source used for this analysis. (D) Absolute counts by subtype.

### 3.2 Baseline performance of the immunohistochemical surrogate

The immunohistochemical surrogate was classifiable in 4,694 of 5,377 tumours (87.3%), but surrogate applicability varied materially across cohorts because full 4-class assignment required a proliferation variable in HR-positive/HER2-negative disease. This limitation had little impact in METABRIC and the SCAN-B cohorts, but reduced classifiability substantially in TCGA-BRCA, where grade was unavailable and Ki-67 was absent.

In METABRIC, the surrogate achieved macro-F1 0.646 (95% CI 0.623-0.672; n=1,554) in the receptor-only matched subset and 0.644 (0.616-0.669; n=1,544) in the receptor-grade matched subset used for comparison with XGBoost plus grade. Concordance was highest for Basal-like tumours, moderate for HER2-enriched tumours, and clearly lower for luminal disease.

The dominant error pattern was crossover at the Luminal A/Luminal B boundary. In METABRIC, 42.5% of molecular Luminal B tumours received a Luminal A-like surrogate label, while 26.9% of molecular Luminal A tumours were overcalled as Luminal B-like (Fig. 2, Table 2). The same general pattern was observed across cohorts. TCGA-BRCA estimates were treated as descriptive only because luminal crossover was based on a small surrogate-classifiable luminal subset (Luminal A n=28; Luminal B n=25), reflecting absence of grade and Ki-67 for most HR-positive/HER2-negative tumours.

**Fig. 2.** Luminal A/B crossover by IHC surrogate across cohorts. TCGA-BRCA is marked with an asterisk because estimates are based on a small surrogate-classifiable luminal subset in the absence of grade and Ki-67.

**Table 2.** Luminal A/Luminal B crossover rates by cohort.

### 3.3 Machine-learning models did not outperform the surrogate

No machine-learning model outperformed the immunohistochemical surrogate in any external matched head-to-head comparison.

In METABRIC, the best receptor-only model (XGBoost) achieved macro-F1 0.523 (95% CI 0.503-0.544), substantially below the surrogate. Adding grade improved performance, with random forest and XGBoost showing similar receptor-grade macro-F1 values after rounding; XGBoost was retained for the primary grey-zone analysis because it had the best unrounded performance and provided the prespecified probability-based confidence score. XGBoost reached 0.559 (0.533-0.584) in the receptor-grade matched subset, but this remained below the matched surrogate value of 0.644 in the same evaluable cases. In paired bootstrap analysis, the receptor-grade XGBoost minus surrogate macro-F1 difference was -0.085 (95% CI -0.107 to -0.062).

In TCGA-BRCA, external comparison was intrinsically constrained because only a limited subset was surrogate-classifiable in the absence of grade and Ki-67. Within this matched subset (n=162), the surrogate achieved macro-F1 0.485 (0.431–0.541), whereas the best machine-learning model reached 0.368. Accordingly, TCGA-BRCA should be interpreted as a structurally limited external validation cohort, while METABRIC provides the cleanest external comparison.

Overall, additional routine variables recovered some signal where available, but this gain was insufficient to match the conventional surrogate.

**Fig. 3.** Matched head-to-head macro-F1 comparisons with bootstrap 95% confidence intervals. Each comparison was restricted to the identical subset classifiable by both the machine-learning model and the IHC surrogate. METABRIC receptor-only: n=1,554; METABRIC receptor-grade: n=1,544; TCGA-BRCA receptor-only: n=162. Paired delta macro-F1 for METABRIC receptor-grade XGBoost versus surrogate was -0.085 (95% CI -0.107 to -0.062).

### 3.4 Confusion-matrix analysis

Normalised confusion matrices in METABRIC (Fig. 4) showed that routine-data approaches captured broad non-luminal biology better than fine luminal subclassification. The surrogate showed high sensitivity for Basal-like tumours and moderate sensitivity for HER2-enriched tumours, but remained limited at the Luminal A/Luminal B boundary. XGBoost receptor-only almost never predicted Luminal B. Adding grade increased Luminal B sensitivity, but reduced Luminal A sensitivity, indicating a trade-off rather than a net increase in recoverable luminal information.

**Fig. 4.** Normalised confusion matrices on METABRIC. (A) IHC surrogate. (B) XGBoost receptor-only. (C) XGBoost receptor-grade.

### 3.5 Grey-zone analysis

Prediction confidence revealed a clinically meaningful low-certainty subgroup in the METABRIC receptor-grade evaluable subset. Using XGBoost receptor-grade maximum predicted class probability as an uncalibrated model-confidence score, 13.5% of cases (n=208) had a maximum class probability <0.50. These tumours were predominantly luminal (73.6%) and showed only 15.9% machine-learning accuracy, while the surrogate still reached 54.8% accuracy in the same subset (Fig. 5, Table 3).

By contrast, in the high-confidence zone (>0.70; 58.2% of cases), machine learning and the surrogate performed similarly (73.1% versus 73.8%). The grey-zone framework therefore identifies a specific subgroup, predominantly luminal disease, in which routine-data-based approximation is least reliable and molecular testing is most likely to clarify intrinsic subtype assignment.

**Fig. 5.** Grey-zone analysis in the METABRIC receptor-grade evaluable subset (n=1,544) using XGBoost receptor-grade maximum predicted class probability as an uncalibrated model-confidence score. (A) Accuracy by confidence zone. (B) Distribution of cases. (C) Luminal A+B proportion by confidence zone.

**Table 3.** Grey-zone analysis by model-confidence tier in the METABRIC receptor-grade evaluable subset (n=1,544).

### 3.6 Sensitivity analysis: 3-class collapse

Collapsing Luminal A and Luminal B into a single luminal class substantially improved performance. Using the best receptor-only model (XGBoost) on the largest evaluable subsets, macro-F1 increased from 0.514 to 0.777 in TCGA-BRCA (n=435) and from 0.522 to 0.767 in METABRIC (n=1,608) (Table 4). This result is central to interpretation: most of the classification deficit resides within the luminal boundary rather than in the broader separation of luminal, HER2-enriched, and Basal-like disease.

The 4-class XGBoost receptor-only values in Table 4 (0.514 and 0.522) correspond to the full model-evaluable subsets and are therefore not directly comparable to the matched head-to-head values reported in Section 3.3 (0.559 for XGBoost receptor-grade, n=1,544), which use a different feature set and a different denominator.

**Table 4.** Sensitivity analysis comparing 4-class XGBoost receptor-only performance with 3-class luminal-grouped performance in model-evaluable subsets. *All values refer to XGBoost receptor-only (ER, PR, HER2) applied to the largest model-evaluable subset in each cohort. The 4-class macro-F1 values (0.514 and 0.522) are therefore not directly comparable to the matched head-to-head results in Section 3.3, which use XGBoost receptor-grade (+grade) on a different denominator (n=1,544 in METABRIC). All direct surrogate-versus-model comparisons are reported separately using identical denominators.*

### 3.7 Information ceiling

Taken together, the results indicate an information ceiling imposed by routine clinicopathological variables. We use "information ceiling" to denote the maximum externally validated performance observed when increasingly complex classifiers are trained on the same routine clinicopathological variables. Adding grade in external validation, and Ki-67 in supportive development analyses, produced only incremental gains, with externally validated performance remaining below the surrogate and well below molecular classification. The limiting factor was therefore not model choice, but information content in the inputs (Supplementary Fig. S5).

## 4. Discussion

This multicohort in silico study shows that routine clinicopathological variables do not contain enough stable information to reliably reproduce 4-class PAM50 intrinsic subtypes across independent cohorts. Three findings define this conclusion: surrogate-to-PAM50 agreement was incomplete across cohorts; most errors concentrated at the Luminal A/Luminal B boundary; and machine-learning models did not consistently improve on the surrogate in external validation.

The negative result is therefore the main result. Machine learning did not fail because the algorithms were intrinsically inadequate; rather, the routine variables themselves appear insufficiently informative for stable 4-class reconstruction of intrinsic biology. This distinction matters. It shifts the interpretation away from model optimisation and toward the practical limit of what routine pathology can encode.

The luminal boundary was the key bottleneck. Biologically, the distinction between Luminal A and Luminal B reflects a continuous proliferative gradient driven by coordinated gene-expression programs [1]. In contrast, routine pathology compresses this axis into much coarser markers such as Ki-67 and histological grade. Even when both variables were available, the gap was narrowed only modestly. The sensitivity analysis supports this interpretation: once Luminal A and Luminal B were collapsed, performance rose sharply in both validation cohorts, indicating that broad luminal versus non-luminal separation is recoverable, while fine luminal subclassification is not.

This finding has potential clinical implications. Tumours with clearly non-luminal phenotypes are already reasonably well captured by routine biomarkers. By contrast, hormone receptor-positive/HER2-negative tumours near the Luminal A/Luminal B boundary remain the main zone of residual routine-data uncertainty [5,6,15]. The grey-zone analysis helps identify where routine methods are least trustworthy and where molecular testing is most likely to alter biological interpretation.

Our study also offers a broader methodological lesson. Algorithmic complexity cannot fully compensate for information-poor inputs. Future efforts should focus less on increasingly complex classifiers built on the same routine variables and more on identifying what additional information—continuous biomarker measures, digital pathology, or true molecular data—is required to break the ceiling.

### 4.1 Relation to prior work

Prior studies have shown incomplete concordance between immunohistochemical surrogates and PAM50, particularly in luminal disease [5,6,15]. Our results extend that literature by testing multiple machine-learning approaches rather than only rule-based surrogates, requiring strict external validation across independent cohorts and platforms, and using head-to-head comparisons on identical evaluable subsets.

Recent work on CorePAM, a 24-gene PAM50-derived expression score, suggests that compact expression-based assays may retain clinically relevant molecular information across RNA-seq and microarray cohorts [16]. In the context of the present study, such approaches are most relevant not as replacements for PAM50, but as potential escalation tools for cases in which routine pathology is least informative. Whether compact molecular assays can resolve grey-zone subtype ambiguity requires direct prospective evaluation.

### 4.2 Strengths and limitations

Strengths include the use of four independent cohorts spanning two molecular platforms, strict external validation, matched-denominator comparisons, bootstrap confidence intervals for macro-F1 and kappa, and a grey-zone framework that translates model uncertainty into potential clinical utility.

Limitations include: most routine biomarkers were available only in simplified categorical format; continuous Ki-67 was available only in the smaller SCAN-B cohort; histological grade was absent in TCGA-BRCA; PAM50 labels were obtained from public resources with cohort-specific implementations; and this was a purely in silico study without outcome-based confirmation of clinical consequences. These limitations reflect the conditions under which routine surrogate subtyping is commonly used in practice.

## 5. Conclusions

Routine clinicopathological variables impose an information ceiling that prevents reliable reproduction of 4-class PAM50 intrinsic subtypes. Machine-learning models do not overcome this limitation because the main constraint lies in the input data rather than the classifier. The residual uncertainty concentrates at the Luminal A/Luminal B boundary, defining a clinically meaningful grey zone in which molecular testing is most likely to refine biological classification and may add practical value. Compact expression-based assays may be operationally feasible, but whether they resolve subtype ambiguity in the grey-zone population requires direct prospective evaluation.

## References

[1] Parker JS, Mullins M, Cheang MC et al (2009) Supervised risk predictor of breast cancer based on intrinsic subtypes. J Clin Oncol 27:1160-1167. https://doi.org/10.1200/JCO.2008.18.1370

[2] Perou CM, Sorlie T, Eisen MB et al (2000) Molecular portraits of human breast tumours. Nature 406:747-752. https://doi.org/10.1038/35021093

[3] Prat A, Pineda E, Adamo B et al (2015) Clinical implications of the intrinsic molecular subtypes of breast cancer. Breast 24:S26-S35. https://doi.org/10.1016/j.breast.2015.07.008

[4] Goldhirsch A, Winer EP, Coates AS et al (2013) Personalizing the treatment of women with early breast cancer: highlights of the St Gallen International Expert Consensus on the Primary Therapy of Early Breast Cancer 2013. Ann Oncol 24:2206-2223. https://doi.org/10.1093/annonc/mdt303

[5] Bastien RR, Rodriguez-Lescure A, Ebbert MT et al (2012) PAM50 breast cancer subtyping by RT-qPCR and concordance with standard clinical molecular markers. BMC Med Genomics 5:44. https://doi.org/10.1186/1755-8794-5-44

[6] Prat A, Cheang MC, Martin M et al (2013) Prognostic significance of progesterone receptor-positive tumor cells within immunohistochemically defined luminal A breast cancer. J Clin Oncol 31:203-209. https://doi.org/10.1200/JCO.2012.43.4134

[7] Collins GS, Reitsma JB, Altman DG, Moons KGM (2015) Transparent reporting of a multivariable prediction model for individual prognosis or diagnosis (TRIPOD): the TRIPOD statement. BMJ 350:g7594. https://doi.org/10.1136/bmj.g7594

[8] Collins GS, Moons KGM, Dhiman P et al (2024) TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods. BMJ 385:e078378. https://doi.org/10.1136/bmj-2023-078378

[9] Bossuyt PM, Reitsma JB, Bruns DE et al (2015) STARD 2015: an updated list of essential items for reporting diagnostic accuracy studies. BMJ 351:h5527. https://doi.org/10.1136/bmj.h5527

[10] Brueffer C, Vallon-Christersson J, Grabau D et al (2018) Clinical value of RNA sequencing-based classifiers for prediction of the five conventional breast cancer biomarkers: a SCAN-B report. JCO Precis Oncol 2:1-18. https://doi.org/10.1200/PO.17.00135

[11] Cancer Genome Atlas Network (2012) Comprehensive molecular portraits of human breast tumours. Nature 490:61-70. https://doi.org/10.1038/nature11412

[12] Curtis C, Shah SP, Chin SF et al (2012) The genomic and transcriptomic architecture of 2,000 breast tumours reveals novel subgroups. Nature 486:346-352. https://doi.org/10.1038/nature10983

[13] Breiman L (2001) Random forests. Machine Learning 45:5-32. https://doi.org/10.1023/A:1010933404324

[14] Chen T, Guestrin C (2016) XGBoost: a scalable tree boosting system. In: Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, pp 785-794. https://doi.org/10.1145/2939672.2939785

[15] Chia SK, Bramwell VH, Tu D et al (2012) A 50-gene intrinsic subtype classifier for prognosis and prediction of benefit from adjuvant tamoxifen. Clin Cancer Res 18:4465-4472. https://doi.org/10.1158/1078-0432.CCR-12-0286

[16] Botan RN, de Sousa JB (2026) CorePAM: a 24-gene PAM50-derived expression score with cross-platform external validation for breast cancer prognosis. Breast Cancer Research, in press. https://doi.org/10.1186/s13058-026-02298-5

## Statements and Declarations

### Funding

The authors declare that no funds, grants, or other support were received during the preparation of this manuscript.

### Competing interests

The authors have no relevant financial or non-financial interests to disclose.

### Ethics approval

This study analysed only publicly available, de-identified datasets and involved no direct patient contact or new biological material; therefore, institutional ethics approval was not required.

### Consent to participate

Not applicable.

### Consent to publish

Not applicable.

### Author contributions

Rafael de Negreiros Botan: Conceptualisation, Methodology, Software, Formal analysis, Data curation, Writing - original draft, Visualisation. Sandro José Martins: Validation, Writing - review and editing. João Batista de Sousa: Supervision, Writing - review and editing. All authors read and approved the final manuscript.

### Data and code availability

All datasets analysed in this study are publicly available. GSE81538 and GSE96058 are available through NCBI GEO; TCGA-BRCA and METABRIC clinical data were accessed through cBioPortal. Complete analysis code and reproducibility materials are publicly available at: https://github.com/RafaelBotan/pam50-ihc-ml

### Declaration of generative AI and AI-assisted technologies in the manuscript preparation process

During the preparation of this work, the authors used generative AI tools to assist with code refinement, language editing, and structural revision of the manuscript. After using these tools, the authors reviewed and edited the content as needed and take full responsibility for the content of the manuscript.

---

## Supplementary Material

**Supplementary Fig. S1.** Cohort allocation and 4-class PAM50 evaluable sample sizes.

**Supplementary Fig. S2.** Feature importance for the full-pathology XGBoost model in the SCAN-B development data.

**Supplementary Fig. S3.** Sensitivity analysis: 4-class XGBoost receptor-only versus 3-class luminal-grouped macro-F1.

**Supplementary Fig. S4.** Receptor-only versus receptor-grade model performance in METABRIC model-evaluable subsets. The dashed surrogate line is shown as contextual reference only; direct model-versus-surrogate comparisons are reported in matched subsets in Fig. 3.

**Supplementary Fig. S5.** Conceptual summary of the information ceiling. Performance increases modestly with additional routine features but remains below the molecular reference standard, supporting the interpretation that the principal limitation lies in input information content rather than model architecture. The full-pathology Ki-67 feature set was not externally evaluable in TCGA-BRCA or METABRIC. The PAM50 reference point denotes the reference standard itself, not an externally validated classifier.
