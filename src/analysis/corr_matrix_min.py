# Spearman correlation matrix (selected features) — tiny, student-friendly

import os
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sns.set_context("notebook")


def find_csv():
    # tries common spots
    candidates = [
        "master_processed.csv",
        "data/processed_data/master_processed.csv",
        "src/analysis/master_processed.csv",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    raise FileNotFoundError(
        "Put master_processed.csv next to this script OR in data/processed_data/."
    )


def make_dominant_purpose(df: pd.DataFrame) -> pd.DataFrame:
    if "dominant_purpose" in df.columns:
        return df
    if not {"work_trips", "edu_trips"} <= set(df.columns):
        return df
    # ensure numeric then set labels (object dtype avoids str/float clash)
    df = df.copy()
    for c in ("work_trips", "edu_trips"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["dominant_purpose"] = pd.Series(index=df.index, dtype="object")
    df.loc[df["work_trips"] > df["edu_trips"], "dominant_purpose"] = "Work"
    df.loc[df["edu_trips"] > df["work_trips"], "dominant_purpose"] = "Education"
    return df


def numeric_view(df: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, list[str], list[str]]:
    # coerce to numeric; drop cols with <3 non-null numeric values
    num = df[cols].copy()
    for c in num.columns:
        num[c] = pd.to_numeric(num[c], errors="coerce")
    valid = [c for c in num.columns if num[c].notna().sum() >= 3]
    skipped = [c for c in cols if c not in valid]
    return num[valid], valid, skipped


def plot_corr(corr: pd.DataFrame, title: str, outpath: str):
    os.makedirs(os.path.dirname(outpath) or ".", exist_ok=True)
    # mask upper triangle for cleaner look
    mask = np.triu(np.ones_like(corr, dtype=bool))
    n = len(corr.columns)
    plt.figure(figsize=(min(14, 2 + 0.8 * n), min(12, 2 + 0.8 * n)))
    sns.heatmap(
        corr, mask=mask, vmin=-1, vmax=1, cmap="vlag",
        square=True, annot=True, fmt=".2f", cbar_kws={"shrink": 0.8}
    )
    plt.title(title)
    plt.tight_layout()
    plt.savefig(outpath, dpi=200)
    plt.close()


def main():
    csv = find_csv()
    df = pd.read_csv(csv)
    df = make_dominant_purpose(df)

    # pick columns we care about (keep only those that actually exist)
    wanted = [
        "avg_trip_distance", "avg_trip_duration", "peak_hour_ratio",
        "total_trips", "total_distance", "total_travel_time",
        "work_trips", "edu_trips",
        "vehicle_per_person", "household_income", "personal_income",
        "age_decade", "is_city",
    ]
    cols = [c for c in wanted if c in df.columns]
    if len(cols) < 2:
        raise ValueError("Not enough expected columns found.")

    num, valid, skipped = numeric_view(df, cols)
    if skipped:
        print(f"- skipped non-numeric/empty columns: {', '.join(skipped)}")
    if len(valid) < 2:
        raise ValueError("Not enough numeric columns left for a matrix after coercion.")

    corr = num.corr(method="spearman")
    os.makedirs("figs", exist_ok=True)
    corr_csv = "figs/corr_spearman_selected.csv"
    corr.to_csv(corr_csv, index=True)
    plot_corr(corr, "Spearman correlation (selected features)", "figs/corr_spearman_selected.png")
    print(f"Saved overall matrix: figs/corr_spearman_selected.png\nCSV: {corr_csv}")

    # Per-group matrices if we have the label
    if "dominant_purpose" in df.columns:
        for label in ["Work", "Education"]:
            sub = df[df["dominant_purpose"] == label]
            if len(sub) >= 3:
                sub_num, sub_valid, _ = numeric_view(sub, cols)
                if len(sub_valid) >= 2:
                    c = sub_num.corr(method="spearman")
                    outpng = f"figs/corr_spearman_{label.lower()}.png"
                    outcsv = f"figs/corr_spearman_{label.lower()}.csv"
                    c.to_csv(outcsv, index=True)
                    plot_corr(c, f"Spearman (selected) – {label}", outpng)
                    print(f"Saved {label} matrix: {outpng}\nCSV: {outcsv}")


if __name__ == "__main__":
    main()
