# COMP20008 A2 – Correlation (tiny version)

from pathlib import Path
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.stats import mannwhitneyu, chi2_contingency

sns.set_context("notebook")

# paths
BASE_FILE = Path(__file__).resolve()
HERE = BASE_FILE.parent
REPO = HERE.parent.parent if (HERE.name == "analysis" and HERE.parent.name == "src") else HERE

CANDIDATES = [
    HERE / "master_processed.csv",
    REPO / "data" / "processed_data" / "master_processed.csv",
]
DATA_FILE = next((p for p in CANDIDATES if p.exists()), None)
if DATA_FILE is None:
    raise FileNotFoundError("Put master_processed.csv next to this script OR in data/processed_data/")
FIGS_DIR = REPO / "figs"


def make_dominant_purpose(df):

    # label by whichever trips are higher
    out = df.copy()
    out["dominant_purpose"] = pd.NA
    out.loc[out["work_trips"] > out["edu_trips"], "dominant_purpose"] = "Work"
    out.loc[out["edu_trips"] > out["work_trips"], "dominant_purpose"] = "Education"
    return out.dropna(subset=["dominant_purpose"])  # drop ties


def mw_and_plot(dom, col, label, fname):
    # Mann–Whitney test + boxplot

    if col not in dom.columns:
        print(f"- skip {col}")

        return
    w = dom.loc[dom["dominant_purpose"] == "Work", col].dropna()
    e = dom.loc[dom["dominant_purpose"] == "Education", col].dropna()

    U, p = mannwhitneyu(w, e, alternative="two-sided")
    r = 1 - (2 * U) / (len(w) * len(e))  # rank-biserial

    print(f"{label}: Work={w.median():.2f}, Edu={e.median():.2f} | U={U:.0f}, p={p:.3g}, r={r:.3f}")

    y_cap = np.quantile(pd.concat([w, e]), 0.99)  # tame outliers
    FIGS_DIR.mkdir(exist_ok=True)
    plt.figure(figsize=(8, 5))
    ax = sns.boxplot(data=dom, x="dominant_purpose", y=col)
    ax.set_ylim(0, y_cap)
    ax.set_title(f"{label} by dominant purpose")
    ax.set_xlabel("Dominant purpose"); ax.set_ylabel(label)
    plt.tight_layout(); plt.savefig(FIGS_DIR / fname, dpi=200); plt.close()


def city_vs_purpose(dom):
    # chi-square + Cramer's V + quick bars
    if "is_city" not in dom.columns:
        print("- skip is_city")

        return
    ct = pd.crosstab(dom["is_city"], dom["dominant_purpose"])
    chi2, p, dof, _ = chi2_contingency(ct)
    n = ct.values.sum()
    V = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))


    print(f"City vs purpose: χ²={chi2:.2f}, df={dof}, p={p:.4g}, V={V:.3f}")

    (ct / ct.sum()).T.plot(kind="bar", figsize=(6, 4))
    plt.title("City vs dominant purpose (proportions)")
    plt.ylabel("Proportion"); plt.xlabel("Dominant purpose")
    plt.tight_layout(); plt.savefig(FIGS_DIR / "is_city_vs_purpose.png", dpi=200); plt.close()


def main():

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"Missing {DATA_FILE}")
    df = pd.read_csv(DATA_FILE)
    dom = make_dominant_purpose(df)

    print("Counts:\n", dom["dominant_purpose"].value_counts().to_string(), "\n")

    mw_and_plot(dom, "avg_trip_distance", "Average trip distance (km)", "avg_trip_distance.png")
    mw_and_plot(dom, "avg_trip_duration", "Average trip duration (min)", "avg_trip_duration.png")

    mw_and_plot(dom, "peak_hour_ratio", "Peak-hour ratio", "peak_hour_ratio.png")
    city_vs_purpose(dom)




if __name__ == "__main__":
    main()
