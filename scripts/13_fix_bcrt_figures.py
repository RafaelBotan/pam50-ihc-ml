"""Regenerate BCRT figures that need label and feature-set cleanup.

The original ggplot script is kept in the project, but the current Windows R
installation raises a patchwork/ggplot rendering error. This script regenerates
the affected figures with the same filenames used by the BCRT package builder.
"""

from __future__ import annotations

from pathlib import Path
import re

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parents[1]
FIG_DIR = BASE_DIR / "figures_R"
TABLE_DIR = BASE_DIR / "tables"
PROC_DIR = BASE_DIR / "data" / "processed"
PAM50_ORDER = ["Basal", "Her2", "LumA", "LumB"]
COHORT_ORDER = ["GSE81538", "GSE96058", "TCGA-BRCA", "METABRIC"]


COLORS = {
    "receptor_only": "#ABD9E9",
    "receptor_grade": "#4575B4",
    "full_pathology": "#E7298A",
    "surrogate": "#D73027",
    "ml": "#4575B4",
    "green": "#66A61E",
    "pink": "#E7298A",
}

SUBTYPE_COLORS = {
    "Basal": "#CC79A7",
    "Her2": "#D55E00",
    "LumA": "#0072B2",
    "LumB": "#56B4E9",
}


def load_harmonized() -> pd.DataFrame:
    df = pd.read_csv(PROC_DIR / "harmonized_full.csv")
    return df[df["pam50_label"].isin(PAM50_ORDER)].copy()


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def parse_ci(value: str) -> tuple[float, float]:
    match = re.search(r"\(([-0-9.]+)-([-0-9.]+)\)", str(value))
    if not match:
        raise ValueError(f"Could not parse CI: {value}")
    return float(match.group(1)), float(match.group(2))


def save_figure(fig: plt.Figure, filename: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    for ext in ["png", "pdf"]:
        fig.savefig(FIG_DIR / f"{filename}.{ext}", dpi=600, bbox_inches="tight")
    fig.savefig(
        FIG_DIR / f"{filename}.tiff",
        dpi=600,
        bbox_inches="tight",
        pil_kwargs={"compression": "tiff_lzw"},
    )
    plt.close(fig)


def fig_cohort_design() -> None:
    df = load_harmonized()
    counts = df.groupby("cohort").size().reindex(COHORT_ORDER)
    colors = ["#7FC97F", "#7FC97F", "#80B1D3", "#80B1D3"]
    labels = ["Development", "Development", "External validation", "External validation"]

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    x = np.arange(len(COHORT_ORDER))
    bars = ax.bar(x, counts.values, color=colors, edgecolor="black", linewidth=0.7, width=0.62)
    for bar, value in zip(bars, counts.values):
        ax.text(bar.get_x() + bar.get_width() / 2, value + 75, f"{int(value):,}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax.set_xticks(x, COHORT_ORDER, rotation=0)
    ax.set_ylabel("4-class PAM50 tumours", fontweight="bold")
    ax.set_ylim(0, max(counts.values) * 1.18)
    ax.grid(axis="y", color="#E6E6E6")
    ax.set_axisbelow(True)
    handles = [
        plt.Rectangle((0, 0), 1, 1, facecolor="#7FC97F", edgecolor="black", label="Development"),
        plt.Rectangle((0, 0), 1, 1, facecolor="#80B1D3", edgecolor="black", label="External validation"),
    ]
    ax.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.12))
    save_figure(fig, "fig1_cohort_design")


def fig_cohort_characteristics() -> None:
    df = load_harmonized()
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.0))
    axes = axes.ravel()

    # A. PAM50 subtype distribution.
    subtype_counts = (
        df.groupby(["cohort", "pam50_label"]).size().unstack(fill_value=0).reindex(COHORT_ORDER).reindex(columns=PAM50_ORDER, fill_value=0)
    )
    subtype_props = subtype_counts.div(subtype_counts.sum(axis=1), axis=0)
    bottom = np.zeros(len(COHORT_ORDER))
    x = np.arange(len(COHORT_ORDER))
    for subtype in PAM50_ORDER:
        axes[0].bar(x, subtype_props[subtype], bottom=bottom, color=SUBTYPE_COLORS[subtype], edgecolor="white", linewidth=0.4, label={"Basal": "Basal-like", "Her2": "HER2-enriched", "LumA": "Luminal A", "LumB": "Luminal B"}[subtype])
        bottom += subtype_props[subtype].values
    axes[0].set_title("A", loc="left", fontweight="bold")
    axes[0].set_ylabel("Proportion", fontweight="bold")
    axes[0].set_xticks(x, COHORT_ORDER, rotation=20, ha="right")
    axes[0].set_ylim(0, 1)
    axes[0].legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=8)

    # B. ER and HER2 positivity rates.
    er = (df["er_status"] == "Positive").groupby(df["cohort"]).mean().reindex(COHORT_ORDER)
    her2 = (df["her2_status"] == "Positive").groupby(df["cohort"]).mean().reindex(COHORT_ORDER)
    width = 0.34
    axes[1].bar(x - width / 2, er, width, color="#4575B4", edgecolor="black", linewidth=0.4, label="ER+")
    axes[1].bar(x + width / 2, her2, width, color="#FC8D59", edgecolor="black", linewidth=0.4, label="HER2+")
    for xpos, val in zip(x - width / 2, er):
        axes[1].text(xpos, val + 0.025, f"{val*100:.0f}%", ha="center", fontsize=8)
    for xpos, val in zip(x + width / 2, her2):
        axes[1].text(xpos, val + 0.025, f"{val*100:.0f}%", ha="center", fontsize=8)
    axes[1].set_title("B", loc="left", fontweight="bold")
    axes[1].set_ylabel("Positivity rate", fontweight="bold")
    axes[1].set_xticks(x, COHORT_ORDER, rotation=20, ha="right")
    axes[1].set_ylim(0, 1.08)
    axes[1].legend(loc="upper center", ncol=2, frameon=False)

    # C. Histological grade distribution.
    grade_df = df[df["grade"].notna()].copy()
    grade_df["grade_label"] = "Grade " + grade_df["grade"].astype(int).astype(str)
    grade_order = ["Grade 1", "Grade 2", "Grade 3"]
    grade_counts = grade_df.groupby(["cohort", "grade_label"]).size().unstack(fill_value=0).reindex(COHORT_ORDER).reindex(columns=grade_order, fill_value=0)
    grade_props = grade_counts.div(grade_counts.sum(axis=1).replace(0, np.nan), axis=0)
    bottom = np.zeros(len(COHORT_ORDER))
    grade_colors = {"Grade 1": "#66BD63", "Grade 2": "#FEE08B", "Grade 3": "#D73027"}
    for grade in grade_order:
        vals = grade_props[grade].fillna(0).values
        axes[2].bar(x, vals, bottom=bottom, color=grade_colors[grade], edgecolor="white", linewidth=0.4, label=grade)
        bottom += vals
    tcga_idx = COHORT_ORDER.index("TCGA-BRCA")
    axes[2].text(tcga_idx, 0.5, "Grade\nnot available", ha="center", va="center", fontsize=9, color="0.35")
    axes[2].set_title("C", loc="left", fontweight="bold")
    axes[2].set_ylabel("Proportion", fontweight="bold")
    axes[2].set_xticks(x, COHORT_ORDER, rotation=20, ha="right")
    axes[2].set_ylim(0, 1)
    axes[2].legend(loc="center left", bbox_to_anchor=(1.01, 0.5), frameon=False, fontsize=8)

    # D. Absolute counts by subtype.
    bottom = np.zeros(len(COHORT_ORDER))
    for subtype in PAM50_ORDER:
        axes[3].bar(x, subtype_counts[subtype], bottom=bottom, color=SUBTYPE_COLORS[subtype], edgecolor="white", linewidth=0.4, label={"Basal": "Basal-like", "Her2": "HER2-enriched", "LumA": "Luminal A", "LumB": "Luminal B"}[subtype])
        bottom += subtype_counts[subtype].values
    for i, total in enumerate(subtype_counts.sum(axis=1).values):
        axes[3].text(i, total + max(subtype_counts.sum(axis=1).values) * 0.025, f"{int(total):,}", ha="center", fontsize=9, fontweight="bold")
    axes[3].set_title("D", loc="left", fontweight="bold")
    axes[3].set_ylabel("Number of tumours", fontweight="bold")
    axes[3].set_xticks(x, COHORT_ORDER, rotation=20, ha="right")
    axes[3].set_ylim(0, max(subtype_counts.sum(axis=1).values) * 1.14)

    for ax in axes:
        ax.grid(axis="y", color="#E6E6E6")
        ax.set_axisbelow(True)
    fig.tight_layout()
    save_figure(fig, "fig2_cohort_characteristics")


def fig_luminal_crossover() -> None:
    df = pd.read_csv(TABLE_DIR / "table_lumAB_crossover.csv")
    cohorts = ["GSE81538", "GSE96058", "TCGA-BRCA", "METABRIC"]
    labels = ["GSE81538", "GSE96058", "TCGA-BRCA*", "METABRIC"]
    lum_a = []
    lum_b = []
    for cohort in cohorts:
        row = df[df["Cohort"] == cohort].iloc[0]
        lum_a.append(float(re.search(r"\(([-0-9.]+)%\)", row["LumA misclassified as LumB"]).group(1)) / 100)
        lum_b.append(float(re.search(r"\(([-0-9.]+)%\)", row["LumB misclassified as LumA"]).group(1)) / 100)

    x = np.arange(len(cohorts))
    width = 0.32
    fig, ax = plt.subplots(figsize=(9, 5.5))
    b1 = ax.bar(
        x - width / 2,
        lum_a,
        width,
        label="LumA misclassified as LumB",
        color="#91BFDB",
        edgecolor="black",
        linewidth=0.6,
    )
    b2 = ax.bar(
        x + width / 2,
        lum_b,
        width,
        label="LumB misclassified as LumA",
        color="#4575B4",
        edgecolor="black",
        linewidth=0.6,
    )
    for bars in [b1, b2]:
        for bar in bars:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                min(h + 0.012, 1.015),
                f"{h * 100:.1f}%",
                ha="center",
                va="bottom",
                fontsize=9,
            )
    ax.set_xticks(x, labels)
    ax.set_ylim(0, 1.08)
    ax.set_yticks(np.linspace(0, 1, 5))
    ax.set_yticklabels([f"{int(v * 100)}%" for v in np.linspace(0, 1, 5)])
    ax.set_ylabel("Misclassification rate", fontweight="bold")
    ax.grid(axis="y", color="#E6E6E6")
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.12))
    save_figure(fig, "fig4_luminal_crossover")


def fig_forest_h2h() -> None:
    df = pd.read_csv(TABLE_DIR / "table_main_results.csv")
    rows = []
    feature_map = {"Set 1": "receptor-only", "Set 2": "receptor-grade"}
    for _, row in df[df["Model"].str.contains("H2H", regex=False)].iterrows():
        lo, hi = parse_ci(row["F1 95% CI"])
        model = row["Model"].replace(" (H2H)", "")
        feature = feature_map.get(row["Feature Set"], row["Feature Set"])
        if "Surrogate" in model:
            label = f"IHC surrogate\nmatched {feature}"
            group = "Surrogate"
        else:
            label = f"{model}\n{feature}"
            group = "ML"
        rows.append(
            {
                "cohort": row["Cohort"],
                "label": label,
                "group": group,
                "f1": float(row["Macro F1"]),
                "lo": lo,
                "hi": hi,
            }
        )
    plot_df = pd.DataFrame(rows)
    cohorts = ["METABRIC", "TCGA-BRCA"]

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    for ax, cohort in zip(axes, cohorts):
        sub = plot_df[plot_df["cohort"] == cohort].iloc[::-1].reset_index(drop=True)
        y = np.arange(len(sub))
        colors = [COLORS["surrogate"] if g == "Surrogate" else COLORS["ml"] for g in sub["group"]]
        for i, row in sub.iterrows():
            ax.errorbar(
                row["f1"],
                y[i],
                xerr=[[row["f1"] - row["lo"]], [row["hi"] - row["f1"]]],
                fmt="D",
                markersize=6,
                color=colors[i],
                ecolor=colors[i],
                elinewidth=2,
                capsize=6,
            )
            ax.text(row["hi"] + 0.008, y[i], f"{row['f1']:.3f}", va="center", ha="left", fontsize=9, color=colors[i])
        ax.axvline(0.5, color="0.6", linestyle="--", linewidth=1)
        ax.set_yticks(y, sub["label"])
        ax.set_title(cohort, fontweight="bold", pad=8)
        ax.grid(axis="x", color="#E6E6E6")
        ax.set_axisbelow(True)
    axes[-1].set_xlabel("Macro-F1", fontweight="bold")
    axes[-1].set_xlim(0.25, 0.76)
    handles = [
        plt.Line2D([0], [0], color=COLORS["ml"], marker="D", linestyle="-", label="ML"),
        plt.Line2D([0], [0], color=COLORS["surrogate"], marker="D", linestyle="-", label="Surrogate"),
    ]
    fig.legend(handles=handles, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.02))
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    save_figure(fig, "fig3_forest_h2h")


def fig_sensitivity() -> None:
    df = pd.read_csv(TABLE_DIR / "table_sensitivity_enhanced.csv")
    order = ["METABRIC", "TCGA-BRCA"]
    analysis_order = ["3-class (Luminal grouped)", "4-class XGBoost receptor-only"]
    label_map = {
        "3-class (Luminal grouped)": "3-class\n(luminal grouped)",
        "4-class XGBoost receptor-only": "4-class\nXGBoost receptor-only",
    }
    colors = {"3-class (Luminal grouped)": COLORS["green"], "4-class XGBoost receptor-only": COLORS["pink"]}

    x = np.arange(len(order))
    width = 0.34
    fig, ax = plt.subplots(figsize=(7.2, 5.4))
    for j, analysis in enumerate(analysis_order):
        vals, los, his = [], [], []
        for cohort in order:
            row = df[(df["Cohort"] == cohort) & (df["Analysis"] == analysis)].iloc[0]
            lo, hi = parse_ci(row["F1 95% CI"])
            vals.append(float(row["Macro F1"]))
            los.append(lo)
            his.append(hi)
        xpos = x + (j - 0.5) * width
        bars = ax.bar(xpos, vals, width, label=label_map[analysis], color=colors[analysis], edgecolor="black", linewidth=0.6)
        ax.errorbar(xpos, vals, yerr=[np.array(vals) - np.array(los), np.array(his) - np.array(vals)], fmt="none", ecolor="black", capsize=5, linewidth=1.5)
        for bar, hi, val in zip(bars, his, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, hi + 0.015, f"{val:.3f}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x, order)
    ax.set_ylabel("Macro-F1", fontweight="bold")
    ax.set_ylim(0, 0.92)
    ax.grid(axis="y", color="#E6E6E6")
    ax.set_axisbelow(True)
    ax.legend(loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.13))
    save_figure(fig, "fig7_sensitivity_3v4")


def fig_feature_set_comparison() -> None:
    df = pd.read_csv(TABLE_DIR / "table_main_results.csv")
    df = df[(df["Cohort"] == "METABRIC") & (~df["Model"].str.contains("H2H", regex=False))].copy()
    df = df[df["Feature Set"].isin(["Set 1", "Set 2"])]
    models = ["Logistic Regression", "Random Forest", "XGBoost"]
    feature_sets = ["Set 1", "Set 2"]
    label_map = {"Set 1": "Receptor-only", "Set 2": "Receptor-grade"}
    colors = {"Set 1": COLORS["receptor_only"], "Set 2": COLORS["receptor_grade"]}

    x = np.arange(len(models))
    width = 0.34
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    for j, fs in enumerate(feature_sets):
        vals, los, his = [], [], []
        for model in models:
            row = df[(df["Model"] == model) & (df["Feature Set"] == fs)].iloc[0]
            lo, hi = parse_ci(row["F1 95% CI"])
            vals.append(float(row["Macro F1"]))
            los.append(lo)
            his.append(hi)
        xpos = x + (j - 0.5) * width
        bars = ax.bar(xpos, vals, width, label=label_map[fs], color=colors[fs], edgecolor="black", linewidth=0.6)
        ax.errorbar(xpos, vals, yerr=[np.array(vals) - np.array(los), np.array(his) - np.array(vals)], fmt="none", ecolor="black", capsize=5, linewidth=1.5)
        for bar, hi, val in zip(bars, his, vals):
            ax.text(bar.get_x() + bar.get_width() / 2, hi + 0.014, f"{val:.3f}", ha="center", va="bottom", fontsize=9)
    ax.axhline(0.645, color=COLORS["surrogate"], linestyle=(0, (6, 6)), linewidth=1.4)
    ax.text(2.25, 0.685, "IHC surrogate\n0.644-0.646", color=COLORS["surrogate"], ha="center", va="center", fontsize=9, style="italic", bbox={"facecolor": "white", "edgecolor": "0.8", "boxstyle": "round,pad=0.25"})
    ax.set_xticks(x, models)
    ax.set_ylabel("Macro-F1", fontweight="bold")
    ax.set_ylim(0, 0.72)
    ax.grid(axis="y", color="#E6E6E6")
    ax.set_axisbelow(True)
    ax.legend(title="Pathology feature set", loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.16))
    save_figure(fig, "fig8_feature_set_comparison")


def fig_information_ceiling() -> None:
    labels = ["Receptor-only\nER/PR/HER2", "Receptor-grade\n+ grade", "Full pathology\n+ Ki-67", "IHC\nsurrogate", "PAM50\nreference\nstandard"]
    x = np.arange(1, 6)
    f1 = [0.523, 0.559, np.nan, 0.645, 1.0]
    types = ["ML", "ML", "ML", "Surrogate", "Reference"]
    colors = {"ML": COLORS["ml"], "Surrogate": "#1B9E77", "Reference": "#D73027"}

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.axhspan(0, 0.65, xmin=0.06, xmax=0.70, color="#4575B4", alpha=0.06)
    ax.axhline(0.645, color="#1B9E77", linestyle=(0, (1, 5)), linewidth=1.5, alpha=0.75)
    ax.text(2.0, 0.035, "Information ceiling zone", color="#4575B4", fontsize=11, style="italic", ha="center")
    for xi, yi, kind in zip(x, f1, types):
        if np.isnan(yi):
            continue
        ax.vlines(xi, 0, yi, colors=colors[kind], linewidth=3, alpha=0.55)
        ax.scatter(xi, yi, s=180, color=colors[kind], zorder=3)
        label = "reference" if kind == "Reference" else ("0.644-0.646" if kind == "Surrogate" else f"{yi:.3f}")
        ax.text(xi, min(yi + 0.035, 1.04), label, color=colors[kind], ha="center", va="bottom", fontweight="bold")
    ax.text(3, 0.12, "not externally\nevaluable", ha="center", va="center", fontsize=9, color="0.35", style="italic")
    ax.set_xticks(x, labels)
    ax.set_ylabel("Macro-F1 (METABRIC)", fontweight="bold")
    ax.set_xlabel("Information source", fontweight="bold")
    ax.set_ylim(0, 1.08)
    ax.grid(axis="y", color="#E6E6E6")
    ax.set_axisbelow(True)
    handles = [plt.Line2D([0], [0], color=colors[k], marker="o", linestyle="-", linewidth=2, markersize=8, label=k) for k in ["ML", "Reference", "Surrogate"]]
    ax.legend(handles=handles, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.13))
    save_figure(fig, "fig10_information_ceiling")


def main() -> None:
    fig_cohort_design()
    fig_cohort_characteristics()
    fig_luminal_crossover()
    fig_forest_h2h()
    fig_sensitivity()
    fig_feature_set_comparison()
    fig_information_ceiling()
    print("Regenerated BCRT figure fixes in", FIG_DIR)


if __name__ == "__main__":
    main()
