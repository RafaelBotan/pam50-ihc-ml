# =========================================================
# PAM50 SURROGATE MANUSCRIPT - HIGH-QUALITY FIGURES (R/ggplot2)
# =========================================================
# Real data from the study results
# Output: TIFF 600 dpi, PDF vector, PNG 600 dpi
# =========================================================

# -------------------------
# 0. SETUP
# -------------------------
library(tidyverse)
library(patchwork)
library(scales)
library(glue)
library(forcats)
library(RColorBrewer)
library(ggtext)
library(grid)
library(gridExtra)

# Set working directory
setwd("Y:/IHQ e PAM50")

# -------------------------
# 1. GLOBAL STYLE
# -------------------------
base_size <- 11
base_family <- "sans"

journal_theme <- theme_minimal(base_size = base_size, base_family = base_family) +
  theme(
    plot.title = element_text(face = "bold", size = 13, hjust = 0),
    plot.subtitle = element_text(size = 10, color = "grey30", hjust = 0),
    plot.caption = element_text(size = 8, color = "grey40", hjust = 0),
    axis.title = element_text(face = "bold", size = 10),
    axis.text = element_text(color = "black", size = 9),
    panel.grid.minor = element_blank(),
    panel.grid.major.x = element_blank(),
    legend.position = "right",
    legend.title = element_text(face = "bold", size = 9),
    legend.text = element_text(size = 8.5),
    strip.text = element_text(face = "bold", size = 10),
    strip.background = element_rect(fill = "grey92", color = NA),
    plot.margin = margin(8, 12, 8, 8)
  )

theme_set(journal_theme)

pal_subtype <- c(
  "Basal-like" = "#D73027",
  "HER2-enriched" = "#FC8D59",
  "Luminal A" = "#4575B4",
  "Luminal B" = "#91BFDB"
)

pal_model <- c(
  "IHC surrogate" = "#1B9E77",
  "Logistic regression" = "#7570B3",
  "Random forest" = "#D95F02",
  "XGBoost" = "#E7298A"
)

# -------------------------
# 2. SAVE HELPER
# -------------------------
save_figure <- function(plot_obj, filename, width = 8, height = 6, dpi = 600) {
  if (!dir.exists("figures_R")) dir.create("figures_R", recursive = TRUE)

  ggsave(
    filename = file.path("figures_R", paste0(filename, ".tiff")),
    plot = plot_obj, width = width, height = height,
    units = "in", dpi = dpi, compression = "lzw", bg = "white"
  )

  ggsave(
    filename = file.path("figures_R", paste0(filename, ".png")),
    plot = plot_obj, width = width, height = height,
    units = "in", dpi = dpi, bg = "white"
  )

  ggsave(
    filename = file.path("figures_R", paste0(filename, ".pdf")),
    plot = plot_obj, width = width, height = height,
    units = "in", device = cairo_pdf, bg = "white"
  )
  message(glue("Saved: {filename}"))
}

# -------------------------
# 3. REAL DATA FROM STUDY
# -------------------------

# Cohort sizes
cohort_sizes <- tibble(
  cohort = c("GSE81538", "GSE96058", "TCGA-BRCA", "METABRIC"),
  source_n = c(405, 3069, 519, 1608),
  analytic_n = c(383, 2867, 519, 1608),
  group = factor(
    c("Training", "Training", "External validation", "External validation"),
    levels = c("Training", "External validation")
  )
)

# Subtype distribution (real data from table1_cohort_characteristics)
subtype_dist <- tribble(
  ~cohort, ~subtype, ~n,
  "GSE81538", "Basal-like", 57,
  "GSE81538", "HER2-enriched", 65,
  "GSE81538", "Luminal A", 156,
  "GSE81538", "Luminal B", 105,
  "GSE96058", "Basal-like", 325,
  "GSE96058", "HER2-enriched", 307,
  "GSE96058", "Luminal A", 1540,
  "GSE96058", "Luminal B", 695,
  "TCGA-BRCA", "Basal-like", 99,
  "TCGA-BRCA", "HER2-enriched", 58,
  "TCGA-BRCA", "Luminal A", 233,
  "TCGA-BRCA", "Luminal B", 129,
  "METABRIC", "Basal-like", 209,
  "METABRIC", "HER2-enriched", 224,
  "METABRIC", "Luminal A", 700,
  "METABRIC", "Luminal B", 475
) %>%
  mutate(
    subtype = factor(subtype, levels = c("Luminal A", "Luminal B", "HER2-enriched", "Basal-like")),
    cohort = factor(cohort, levels = c("GSE81538", "GSE96058", "TCGA-BRCA", "METABRIC"))
  ) %>%
  group_by(cohort) %>%
  mutate(prop = n / sum(n)) %>%
  ungroup()

# Performance data (real results from table_main_results)
performance_df <- tribble(
  ~cohort, ~model, ~feature_set, ~comparison, ~macro_f1, ~f1_lo, ~f1_hi, ~kappa, ~balanced_accuracy,
  # TCGA Set 1
  "TCGA-BRCA", "Logistic regression", "Set 1", "All", 0.491, 0.453, 0.525, 0.409, 0.607,
  "TCGA-BRCA", "Random forest", "Set 1", "All", 0.491, 0.453, 0.525, 0.409, 0.607,
  "TCGA-BRCA", "XGBoost", "Set 1", "All", 0.514, 0.477, 0.547, 0.404, 0.601,
  "TCGA-BRCA", "IHC surrogate", "Set 1", "H2H", 0.485, 0.431, 0.541, 0.489, 0.571,
  "TCGA-BRCA", "Logistic regression", "Set 1", "H2H", 0.368, 0.336, 0.396, 0.428, 0.457,
  # METABRIC Set 1
  "METABRIC", "Logistic regression", "Set 1", "All", 0.433, 0.413, 0.453, 0.318, 0.541,
  "METABRIC", "Random forest", "Set 1", "All", 0.433, 0.413, 0.453, 0.318, 0.541,
  "METABRIC", "XGBoost", "Set 1", "All", 0.522, 0.501, 0.542, 0.376, 0.576,
  "METABRIC", "IHC surrogate", "Set 1", "H2H", 0.646, 0.623, 0.672, 0.471, 0.621,
  "METABRIC", "XGBoost", "Set 1", "H2H", 0.523, 0.503, 0.544, 0.383, 0.579,
  # METABRIC Set 2
  "METABRIC", "Logistic regression", "Set 2", "All", 0.519, 0.495, 0.544, 0.362, 0.574,
  "METABRIC", "Random forest", "Set 2", "All", 0.559, 0.533, 0.583, 0.388, 0.592,
  "METABRIC", "XGBoost", "Set 2", "All", 0.559, 0.533, 0.584, 0.402, 0.585,
  "METABRIC", "IHC surrogate", "Set 2", "H2H", 0.644, 0.616, 0.669, 0.467, 0.618,
  "METABRIC", "XGBoost", "Set 2", "H2H", 0.559, 0.533, 0.584, 0.402, 0.585
)

# Feature importance (real from XGBoost)
feature_importance_df <- tribble(
  ~feature, ~importance,
  "ER", 0.35,
  "HER2", 0.25,
  "Grade", 0.19,
  "Ki-67", 0.13,
  "PR", 0.08
) %>%
  mutate(feature = fct_reorder(feature, importance))

# Luminal A/B crossover (real data)
luminal_crossover <- tribble(
  ~cohort, ~direction, ~rate,
  "GSE81538", "LumB misclassified as LumA", 0.162,
  "GSE81538", "LumA misclassified as LumB", 0.271,
  "GSE96058", "LumB misclassified as LumA", 0.290,
  "GSE96058", "LumA misclassified as LumB", 0.251,
  "TCGA-BRCA", "LumB misclassified as LumA", 0.000,
  "TCGA-BRCA", "LumA misclassified as LumB", 0.929,
  "METABRIC", "LumB misclassified as LumA", 0.425,
  "METABRIC", "LumA misclassified as LumB", 0.269
) %>%
  mutate(cohort = factor(cohort, levels = c("GSE81538", "GSE96058", "TCGA-BRCA", "METABRIC")))

# Grey zone data (real)
grey_zone <- tribble(
  ~zone, ~n, ~pct, ~ml_acc, ~surr_acc, ~luminal_pct,
  "Low (<0.50)", 208, 13.5, 0.159, 0.548, 0.736,
  "Medium (0.50-0.70)", 438, 28.4, 0.493, 0.493, 0.888,
  "High (>0.70)", 898, 58.2, 0.731, 0.738, 0.649
) %>%
  mutate(zone = factor(zone, levels = c("Low (<0.50)", "Medium (0.50-0.70)", "High (>0.70)")))

# 3-class vs 4-class sensitivity (real)
sensitivity_df <- tribble(
  ~cohort, ~analysis, ~macro_f1, ~f1_lo, ~f1_hi,
  "TCGA-BRCA", "4-class", 0.514, 0.477, 0.547,
  "TCGA-BRCA", "3-class (luminal grouped)", 0.777, 0.720, 0.826,
  "METABRIC", "4-class", 0.522, 0.501, 0.542,
  "METABRIC", "3-class (luminal grouped)", 0.767, 0.739, 0.796
)

# ER/HER2 positivity rates (real)
biomarker_rates <- tribble(
  ~cohort, ~marker, ~rate,
  "GSE81538", "ER+", 0.799,
  "GSE81538", "HER2+", 0.226,
  "GSE96058", "ER+", 0.921,
  "GSE96058", "HER2+", 0.134,
  "TCGA-BRCA", "ER+", 0.773,
  "TCGA-BRCA", "HER2+", 0.224,
  "METABRIC", "ER+", 0.805,
  "METABRIC", "HER2+", 0.134
) %>%
  mutate(cohort = factor(cohort, levels = c("GSE81538", "GSE96058", "TCGA-BRCA", "METABRIC")))

# Grade distribution (real)
grade_dist <- tribble(
  ~cohort, ~grade, ~n,
  "GSE81538", "Grade 1", 43,
  "GSE81538", "Grade 2", 154,
  "GSE81538", "Grade 3", 186,
  "GSE96058", "Grade 1", 431,
  "GSE96058", "Grade 2", 1321,
  "GSE96058", "Grade 3", 1060,
  "METABRIC", "Grade 1", 142,
  "METABRIC", "Grade 2", 635,
  "METABRIC", "Grade 3", 767
) %>%
  mutate(
    grade = factor(grade, levels = c("Grade 1", "Grade 2", "Grade 3")),
    cohort = factor(cohort, levels = c("GSE81538", "GSE96058", "METABRIC"))
  ) %>%
  group_by(cohort) %>%
  mutate(prop = n / sum(n)) %>%
  ungroup()


# =============================================================
# FIGURE 1 - STUDY DESIGN / COHORT FLOW
# =============================================================
fig1 <- ggplot(cohort_sizes, aes(x = fct_reorder(cohort, analytic_n), y = analytic_n, fill = group)) +
  geom_col(width = 0.65, color = "black", linewidth = 0.3) +
  geom_text(aes(label = comma(analytic_n)), vjust = -0.4, fontface = "bold", size = 4.2) +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.12))) +
  scale_fill_manual(values = c("Training" = "#7FC97F", "External validation" = "#80B1D3")) +
  labs(
    x = NULL,
    y = "Number of tumours",
    fill = NULL
  ) +
  theme(legend.position = "top")

save_figure(fig1, "fig1_cohort_design", width = 7, height = 5)


# =============================================================
# FIGURE 2 - SUBTYPE DISTRIBUTIONS (multi-panel)
# =============================================================

# Panel A: Stacked bar subtype distribution
p2a <- ggplot(subtype_dist, aes(x = cohort, y = prop, fill = subtype)) +
  geom_col(width = 0.7, color = "white", linewidth = 0.3) +
  scale_y_continuous(labels = percent_format(accuracy = 1), expand = expansion(mult = c(0, 0.02))) +
  scale_fill_manual(values = pal_subtype) +
  labs(title = "A", x = NULL, y = "Proportion", fill = "Subtype") +
  theme(legend.position = "right", axis.text.x = element_text(angle = 20, hjust = 1))

# Panel B: ER/HER2 rates
p2b <- ggplot(biomarker_rates, aes(x = cohort, y = rate, fill = marker)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.6, color = "black", linewidth = 0.2) +
  geom_text(aes(label = sprintf("%.0f%%", rate * 100)),
            position = position_dodge(width = 0.7), vjust = -0.3, size = 3) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 1.05),
                     expand = expansion(mult = c(0, 0))) +
  scale_fill_manual(values = c("ER+" = "#4575B4", "HER2+" = "#FC8D59")) +
  labs(title = "B", x = NULL, y = "Positivity rate", fill = NULL) +
  theme(legend.position = "top", axis.text.x = element_text(angle = 20, hjust = 1))

# Panel C: Grade distribution
p2c <- ggplot(grade_dist, aes(x = cohort, y = prop, fill = grade)) +
  geom_col(width = 0.7, color = "white", linewidth = 0.3) +
  scale_y_continuous(labels = percent_format(accuracy = 1), expand = expansion(mult = c(0, 0.02))) +
  scale_fill_manual(values = c("Grade 1" = "#66BD63", "Grade 2" = "#FEE08B", "Grade 3" = "#D73027")) +
  labs(title = "C", x = NULL, y = "Proportion", fill = NULL) +
  theme(legend.position = "right", axis.text.x = element_text(angle = 20, hjust = 1))

# Panel D: Sample counts
p2d <- ggplot(subtype_dist, aes(x = cohort, y = n, fill = subtype)) +
  geom_col(width = 0.7, color = "white", linewidth = 0.3) +
  geom_text(aes(label = n), position = position_stack(vjust = 0.5), size = 2.8, color = "white", fontface = "bold") +
  scale_y_continuous(labels = comma, expand = expansion(mult = c(0, 0.02))) +
  scale_fill_manual(values = pal_subtype) +
  labs(title = "D", x = NULL, y = "Number of tumours", fill = "Subtype") +
  theme(legend.position = "none", axis.text.x = element_text(angle = 20, hjust = 1))

fig2 <- (p2a + p2b) / (p2c + p2d)

save_figure(fig2, "fig2_cohort_characteristics", width = 12, height = 9)


# =============================================================
# FIGURE 3 - FOREST PLOT (Head-to-Head)
# =============================================================
h2h_data <- performance_df %>%
  filter(comparison == "H2H") %>%
  mutate(
    label = glue("{model} ({feature_set})"),
    is_surrogate = str_detect(model, "surrogate"),
    cohort_set = glue("{cohort} - {feature_set}")
  )

fig3 <- ggplot(h2h_data, aes(x = macro_f1, y = fct_rev(label), color = ifelse(is_surrogate, "Surrogate", "ML"))) +
  geom_vline(xintercept = 0.5, linetype = "dashed", color = "grey60", linewidth = 0.3) +
  geom_errorbarh(aes(xmin = f1_lo, xmax = f1_hi), height = 0.25, linewidth = 0.7) +
  geom_point(size = 3.5, shape = 18) +
  geom_text(aes(label = sprintf("%.3f", macro_f1)), hjust = -0.3, size = 3.2, show.legend = FALSE) +
  facet_wrap(~ cohort, ncol = 1, scales = "free_y") +
  scale_color_manual(values = c("Surrogate" = "#D73027", "ML" = "#4575B4")) +
  scale_x_continuous(limits = c(0.25, 0.75), breaks = seq(0.3, 0.7, 0.1)) +
  labs(
    x = "Macro-F1",
    y = NULL,
    color = NULL
  ) +
  theme(
    legend.position = "top",
    panel.grid.major.y = element_blank(),
    strip.text = element_text(size = 11)
  )

save_figure(fig3, "fig3_forest_h2h", width = 9, height = 7)


# =============================================================
# FIGURE 4 - LUMINAL A/B CROSSOVER
# =============================================================
fig4 <- ggplot(luminal_crossover, aes(x = cohort, y = rate, fill = direction)) +
  geom_col(position = position_dodge(width = 0.75), width = 0.65, color = "black", linewidth = 0.25) +
  geom_text(aes(label = sprintf("%.1f%%", rate * 100)),
            position = position_dodge(width = 0.75), vjust = -0.3, size = 3.3) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 1),
                     expand = expansion(mult = c(0, 0.05))) +
  scale_fill_manual(values = c(
    "LumA misclassified as LumB" = "#91BFDB",
    "LumB misclassified as LumA" = "#4575B4"
  )) +
  labs(
    x = NULL,
    y = "Misclassification rate",
    fill = NULL
  ) +
  theme(legend.position = "top")

save_figure(fig4, "fig4_luminal_crossover", width = 9, height = 5.5)


# =============================================================
# FIGURE 5 - GREY ZONE ANALYSIS (multi-panel)
# =============================================================

# Panel A: Accuracy by zone
gz_acc <- grey_zone %>%
  select(zone, ML = ml_acc, Surrogate = surr_acc) %>%
  pivot_longer(cols = c(ML, Surrogate), names_to = "method", values_to = "accuracy")

p5a <- ggplot(gz_acc, aes(x = zone, y = accuracy, fill = method)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.6, color = "black", linewidth = 0.2) +
  geom_text(aes(label = sprintf("%.1f%%", accuracy * 100)),
            position = position_dodge(width = 0.7), vjust = -0.3, size = 3.2) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 0.85),
                     expand = expansion(mult = c(0, 0))) +
  scale_fill_manual(values = c("ML" = "#4575B4", "Surrogate" = "#1B9E77")) +
  labs(title = "A", x = NULL, y = "Accuracy", fill = NULL) +
  theme(legend.position = "top", axis.text.x = element_text(size = 9))

# Panel B: Case distribution
p5b <- ggplot(grey_zone, aes(x = zone, y = pct / 100)) +
  geom_col(width = 0.6, fill = "#FEE08B", color = "black", linewidth = 0.2) +
  geom_text(aes(label = sprintf("%.1f%%\n(n=%d)", pct, n)), vjust = -0.1, size = 3.2) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 0.72),
                     expand = expansion(mult = c(0, 0))) +
  labs(title = "B", x = NULL, y = "Proportion of cases") +
  theme(axis.text.x = element_text(size = 9))

# Panel C: Luminal proportion
p5c <- ggplot(grey_zone, aes(x = zone, y = luminal_pct)) +
  geom_col(width = 0.6, fill = "#91BFDB", color = "black", linewidth = 0.2) +
  geom_text(aes(label = sprintf("%.1f%%", luminal_pct * 100)), vjust = -0.3, size = 3.2) +
  scale_y_continuous(labels = percent_format(accuracy = 1), limits = c(0, 1),
                     expand = expansion(mult = c(0, 0))) +
  labs(title = "C", x = NULL, y = "Proportion luminal") +
  theme(axis.text.x = element_text(size = 9))

fig5 <- p5a / (p5b + p5c)

save_figure(fig5, "fig5_grey_zone", width = 11, height = 9)


# =============================================================
# FIGURE 6 - FEATURE IMPORTANCE
# =============================================================
fig6 <- ggplot(feature_importance_df, aes(x = importance, y = feature)) +
  geom_col(fill = "#4575B4", width = 0.6, color = "black", linewidth = 0.25) +
  geom_text(aes(label = sprintf("%.2f", importance)), hjust = -0.15, size = 3.8, fontface = "bold") +
  scale_x_continuous(limits = c(0, 0.42), expand = expansion(mult = c(0, 0))) +
  labs(
    x = "Relative importance",
    y = NULL
  ) +
  theme(panel.grid.major.y = element_blank())

save_figure(fig6, "fig6_feature_importance", width = 7, height = 4.5)


# =============================================================
# FIGURE 7 - 4-CLASS vs 3-CLASS SENSITIVITY
# =============================================================
fig7 <- ggplot(sensitivity_df, aes(x = cohort, y = macro_f1, fill = analysis)) +
  geom_col(position = position_dodge(width = 0.7), width = 0.6, color = "black", linewidth = 0.25) +
  geom_errorbar(aes(ymin = f1_lo, ymax = f1_hi),
                position = position_dodge(width = 0.7), width = 0.2, linewidth = 0.4) +
  geom_text(aes(label = sprintf("%.3f", macro_f1)),
            position = position_dodge(width = 0.7), vjust = -1.2, size = 3.5) +
  scale_y_continuous(limits = c(0, 0.95), expand = expansion(mult = c(0, 0.05))) +
  scale_fill_manual(values = c("4-class" = "#E7298A", "3-class (luminal grouped)" = "#66A61E")) +
  labs(
    x = NULL,
    y = "Macro-F1",
    fill = NULL
  ) +
  theme(legend.position = "top")

save_figure(fig7, "fig7_sensitivity_3v4", width = 7, height = 5.5)


# =============================================================
# FIGURE 8 (ADDITIONAL) - PERFORMANCE BY FEATURE SET (METABRIC)
# =============================================================
metabric_perf <- performance_df %>%
  filter(cohort == "METABRIC", comparison == "All") %>%
  mutate(model = factor(model, levels = c("Logistic regression", "Random forest", "XGBoost")))

fig8 <- ggplot(metabric_perf, aes(x = model, y = macro_f1, fill = feature_set)) +
  geom_col(position = position_dodge(width = 0.75), width = 0.65, color = "black", linewidth = 0.2) +
  geom_errorbar(aes(ymin = f1_lo, ymax = f1_hi),
                position = position_dodge(width = 0.75), width = 0.2, linewidth = 0.4) +
  geom_text(aes(label = sprintf("%.3f", macro_f1)),
            position = position_dodge(width = 0.75), vjust = -1.2, size = 3.2) +
  geom_hline(yintercept = 0.646, linetype = "dashed", color = "#D73027", linewidth = 0.6) +
  annotate("text", x = 3.3, y = 0.665, label = "IHC surrogate (0.646)", color = "#D73027",
           size = 3, hjust = 1, fontface = "italic") +
  scale_y_continuous(limits = c(0, 0.75), expand = expansion(mult = c(0, 0.05))) +
  scale_fill_manual(values = c("Set 1" = "#ABD9E9", "Set 2" = "#4575B4")) +
  labs(
    x = NULL,
    y = "Macro-F1",
    fill = "Feature set"
  ) +
  theme(legend.position = "top")

save_figure(fig8, "fig8_feature_set_comparison", width = 8, height = 5.5)


# =============================================================
# FIGURE 9 (ADDITIONAL) - MULTI-METRIC PANEL
# =============================================================
h2h_metrics <- performance_df %>%
  filter(comparison == "H2H", cohort == "METABRIC") %>%
  select(model, feature_set, `Macro-F1` = macro_f1, Kappa = kappa, `Balanced Acc.` = balanced_accuracy) %>%
  pivot_longer(cols = c(`Macro-F1`, Kappa, `Balanced Acc.`), names_to = "metric", values_to = "value") %>%
  mutate(
    is_surrogate = str_detect(model, "surrogate"),
    label = ifelse(is_surrogate, "IHC surrogate", paste0(model, " (", feature_set, ")"))
  )

fig9 <- ggplot(h2h_metrics, aes(x = metric, y = value, fill = label)) +
  geom_col(position = position_dodge(width = 0.75), width = 0.65, color = "black", linewidth = 0.2) +
  geom_text(aes(label = sprintf("%.3f", value)),
            position = position_dodge(width = 0.75), vjust = -0.3, size = 3) +
  scale_y_continuous(limits = c(0, 0.72), expand = expansion(mult = c(0, 0.05))) +
  scale_fill_manual(values = c(
    "IHC surrogate" = "#1B9E77",
    "XGBoost (Set 1)" = "#ABD9E9",
    "XGBoost (Set 2)" = "#E7298A"
  )) +
  labs(
    x = NULL,
    y = "Score",
    fill = NULL
  ) +
  theme(legend.position = "top")

save_figure(fig9, "fig9_multimetric_panel", width = 8.5, height = 5.5)


# =============================================================
# FIGURE 10 (ADDITIONAL) - INFORMATION CEILING CONCEPT
# =============================================================
ceiling_data <- tibble(
  x = c(1, 2, 3, 4, 5),
  label = c("ER/PR/HER2\n(3 binary)", "+Grade\n(+1 ordinal)", "+Ki-67\n(+1 continuous)",
            "IHC\nSurrogate", "PAM50\n(50 genes)"),
  f1 = c(0.523, 0.559, NA, 0.646, 1.0),
  type = c("ML", "ML", "ML", "Surrogate", "Reference")
)

fig10 <- ggplot(ceiling_data %>% filter(!is.na(f1)),
                aes(x = x, y = f1, color = type)) +
  # Ceiling line
  geom_hline(yintercept = 0.646, linetype = "dotted", color = "#1B9E77", linewidth = 0.5, alpha = 0.7) +
  annotate("rect", xmin = 0.5, xmax = 3.5, ymin = 0, ymax = 0.65,
           fill = "#4575B4", alpha = 0.05) +
  annotate("text", x = 2, y = 0.02, label = "Information ceiling zone",
           color = "#4575B4", size = 3.5, fontface = "italic") +
  geom_segment(aes(xend = x, yend = 0), linewidth = 1.5, alpha = 0.6) +
  geom_point(size = 5) +
  geom_text(aes(label = ifelse(!is.na(f1), sprintf("%.3f", f1), "")),
            vjust = -1.2, size = 3.8, fontface = "bold", show.legend = FALSE) +
  scale_x_continuous(breaks = ceiling_data$x, labels = ceiling_data$label) +
  scale_y_continuous(limits = c(0, 1.05), breaks = seq(0, 1, 0.2)) +
  scale_color_manual(values = c("ML" = "#4575B4", "Surrogate" = "#1B9E77", "Reference" = "#D73027")) +
  labs(
    x = "Information source",
    y = "Macro-F1 (METABRIC)",
    color = NULL
  ) +
  theme(
    legend.position = "top",
    panel.grid.major.x = element_blank(),
    axis.text.x = element_text(size = 9)
  )

save_figure(fig10, "fig10_information_ceiling", width = 9, height = 6)


# -------------------------
# SESSION INFO
# -------------------------
writeLines(capture.output(sessionInfo()), con = file.path("figures_R", "sessionInfo.txt"))

message("\n=== All 10 figures generated in figures_R/ ===")
