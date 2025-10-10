"""
Data Clustering & Profiling
Analyses:
  1) Household Profiles
  2) Trip Patterns
  3) Education Journeys
  4) Regional Travel Profiles
  5) Joint Work vs Education (plus diagnostic plots)
Run:
  python src/data_clustering.py
"""

from __future__ import annotations
import os, json, glob
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# repo root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# data and output folders
DATA_DIR = os.path.join(BASE_DIR, "data", "processed_data")
OUT_DIR  = os.path.join(BASE_DIR, "output")
os.makedirs(OUT_DIR, exist_ok=True)

# I/O helpers (CSV + XLSX)
def _read_any(path: str) -> pd.DataFrame | None:
    try:
        if path.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(path, engine="openpyxl")
        return pd.read_csv(path, low_memory=False)
    except Exception as e:
        print(f"Failed to read {os.path.relpath(path)}: {e}")
        return None

#Read from /data/processed_data/. Tries CSV then XLSX (or vice versa).
def try_read(filename: str) -> pd.DataFrame | None:

    name, ext = os.path.splitext(filename)
    candidates = [
        os.path.join(DATA_DIR, filename),
        os.path.join(DATA_DIR, name + ".csv"),
        os.path.join(DATA_DIR, name + ".xlsx"),
        os.path.join(DATA_DIR, name + ".xls"),
    ]
    for p in candidates:
        if os.path.exists(p):
            print(f"📄 Reading: {os.path.relpath(p)}")
            return _read_any(p)
    print(f"File not found in {DATA_DIR}: {filename}")
    return None

# Feature engineering
"""
    Add derived_speed (distance/duration) and dep_hour (0–23) where possible.
    Attempts to detect likely columns by name.
"""
def derive_trip_features(df: pd.DataFrame) -> pd.DataFrame:

    if df is None or df.empty:
        return df

    cols = {c.lower(): c for c in df.columns}

    # distance / duration -> derived_speed
    dist_col = next((cols[c] for c in cols if "dist" in c), None)
    dur_col  = next((cols[c] for c in cols if "dur" in c or ("time" in c and "start" not in c and "end" not in c)), None)
    if dist_col and dur_col:
        dist = pd.to_numeric(df[dist_col], errors="coerce")
        dur  = pd.to_numeric(df[dur_col],  errors="coerce")
        with np.errstate(divide="ignore", invalid="ignore"):
            df["derived_speed"] = np.where(dur > 0, dist / dur, np.nan)

    # departure -> dep_hour
    dep_col = next((cols[c] for c in cols if "depart" in c or "dep_time" in c or "start_time" in c or "starttime" in c), None)
    if dep_col:
        def to_hour(x):
            try:
                if pd.isna(x): return np.nan
                if isinstance(x, (int, float)) and 0 <= x <= 2359:
                    # numeric HHMM -> hour
                    return int(int(x) // 100)
                s = str(x)
                if ":" in s: return int(s.split(":")[0])
                if s.isdigit() and 1 <= len(s) <= 4: return int(int(s)//100)
                # already hour?
                v = float(s)
                return v if 0 <= v < 24 else np.nan
            except:
                return np.nan
        df["dep_hour"] = df[dep_col].apply(to_hour)

    return df

# Clustering
def find_cols(cols, patterns):
    #Return columns whose lowercase name contains any pattern (keeps order)
    out, seen = [], set()
    for c in cols:
        if any(p in c.lower() for p in patterns):
            if c not in seen:
                out.append(c); seen.add(c)
    return out

def best_kmeans(X, k_min=2, k_max=8, random_state=42):
    #Try K=k_min..k_max and return (labels, model, best_k, scores_dict)
    best_score, best = -1.0, (None, None, None, {})
    scores = {}
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, n_init=10, random_state=random_state)
        labels = km.fit_predict(X)
        score = silhouette_score(X, labels) if len(set(labels)) > 1 else -1.0
        scores[k] = float(score)
        if score > best_score:
            best_score, best = score, (labels, km, k, scores.copy())
    return best

def profile_clusters(df, label_col, numeric_cols, categorical_cols):
    prof = {}
    if numeric_cols:
        prof["numeric_means"] = df.groupby(label_col)[numeric_cols].mean().round(3)
    for c in categorical_cols:
        if df[c].nunique(dropna=True) <= 30:
            prof[f"cat_{c}"] = pd.crosstab(df[label_col], df[c], normalize="index").round(3)
    return prof

def plot_cluster_sizes(labels, title, out_path):
    sizes = pd.Series(labels, name="cluster").value_counts().sort_index()
    plt.figure()
    sizes.plot(kind="bar")
    plt.title(title); plt.xlabel("Cluster"); plt.ylabel("Count")
    plt.tight_layout(); plt.savefig(out_path); plt.close()

def run_clustering(name, df, numeric_like, categorical_like, output_prefix, add_trip_deriv=False):
    if df is None or len(df) == 0:
        print(f"{name}:no_data");  return {"status": "no_data"}

    df0 = df.copy()
    if add_trip_deriv:
        df0 = derive_trip_features(df0)

    cols = list(df0.columns)
    num_candidates = find_cols(cols, numeric_like)
    numeric_cols = [c for c in num_candidates if pd.api.types.is_numeric_dtype(df0[c])]

    if not numeric_cols:
        # try coercion
        for c in num_candidates:
            df0[c] = pd.to_numeric(df0[c], errors="coerce")
        numeric_cols = [c for c in num_candidates if pd.api.types.is_numeric_dtype(df0[c])]

    if not numeric_cols:
        numeric_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df0[c])][:6]

    categorical_cols = [c for c in find_cols(cols, categorical_like) if df0[c].nunique(dropna=True) > 1]

    if not numeric_cols:
        print(f"{name}: no_numeric_features");  return {"status": "no_numeric_features"}

    # Prepare matrix (simple dropna for robustness/speed)
    X = df0[numeric_cols].replace([np.inf, -np.inf], np.nan).dropna()
    if X.empty:
        print(f"{name}: after dropna, no rows remain");  return {"status": "no_rows_after_dropna"}
    idx = X.index

    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    labels, model, k, scores = best_kmeans(Xs)
    df_out = df0.copy()
    df_out["cluster"] = np.nan
    df_out.loc[idx, "cluster"] = labels

    profiles = profile_clusters(df_out.loc[idx], "cluster", numeric_cols, categorical_cols)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    labeled_path = os.path.join(OUT_DIR, f"{output_prefix}_labeled_{ts}.csv")
    chart_path   = os.path.join(OUT_DIR, f"{output_prefix}_cluster_sizes_{ts}.png")
    df_out.to_csv(labeled_path, index=False)
    plot_cluster_sizes(labels, f"{name} (K={k})", chart_path)

    print(f"{name}:OK  K={k}  rows={len(X)}  saved -> {os.path.relpath(labeled_path)}")
    return {
        "status": "ok", "k": k, "scores": scores,
        "numeric_cols": numeric_cols, "categorical_cols": categorical_cols,
        "labeled_csv": labeled_path, "chart_png": chart_path,
        "profiles": {k: (v.to_dict() if isinstance(v, pd.DataFrame) else v) for k, v in profiles.items()}
    }

# Joint Work vs Education: plots
def joint_work_edu_plots(joint_csv_path: str):
    joint = pd.read_csv(joint_csv_path)
    assert "cluster" in joint.columns and "trip_type" in joint.columns, \
        "Expected 'cluster' and 'trip_type' in joint file."

    num_patterns = ["dist", "distance", "dur", "duration", "dep_hour", "speed", "length", "time", "trav", "trip"]
    num_cols = [c for c in joint.columns
                if any(p in c.lower() for p in num_patterns) and pd.api.types.is_numeric_dtype(joint[c])]

    # A) composition (stacked bar)
    comp = (pd.crosstab(joint["cluster"], joint["trip_type"], normalize="index")
            .reindex(sorted(joint["cluster"].dropna().unique())))
    plt.figure()
    comp.plot(kind="bar", stacked=True, figsize=(8, 4))
    plt.title("Work vs Education Composition by Cluster")
    plt.xlabel("Cluster"); plt.ylabel("Share")
    plt.tight_layout()
    out_a = os.path.join(OUT_DIR, "joint_clusters_composition.png")
    plt.savefig(out_a); plt.close()

    # B) grouped means for up to 4 numeric features
    chosen = [c for c in num_cols][:4] or ["dep_hour"]
    agg = (joint.groupby(["cluster", "trip_type"])[chosen]
                 .mean()
                 .reset_index())

    for col in chosen:
        pivot = agg.pivot(index="cluster", columns="trip_type", values=col).sort_index()
        plt.figure()
        pivot.plot(kind="bar", figsize=(8, 4))
        plt.title(f"Mean {col} by Cluster and Trip Type")
        plt.xlabel("Cluster"); plt.ylabel(f"Mean {col}")
        plt.tight_layout()
        out_b = os.path.join(OUT_DIR, f"joint_mean_{col}.png")
        plt.savefig(out_b); plt.close()

    print("Saved joint composition and mean plots to ./output")

# Main
def main():
    print("=== Loading datasets from ./data/processed_data ===")
    hh          = try_read("households_processed.csv")
    trips       = try_read("trips_processed.csv")
    wtrips      = try_read("work_trips_processed.csv")
    etrips      = try_read("education_trips_processed.csv")
    journey_edu = try_read("journey_education_processed.csv")
    ptsum       = try_read("persons_trips_summary_processed.csv")
    master      = try_read("master_processed.csv")

    print("Loaded shapes:",
          {"households": None if hh is None else hh.shape,
           "trips": None if trips is None else trips.shape,
           "work_trips": None if wtrips is None else wtrips.shape,
           "education_trips": None if etrips is None else etrips.shape,
           "journey_education": None if journey_edu is None else journey_edu.shape,
           "persons_trips_summary": None if ptsum is None else ptsum.shape,
           "master": None if master is None else master.shape})

    results = {}

    # 1) Household Profiles
    results["households"] = run_clustering(
        "Household Profiles", hh,
        numeric_like=["income","car","veh","trip","hhsize","household_size","age","children","count","freq"],
        categorical_like=["region","area","zone"],
        output_prefix="households_profiles",
        add_trip_deriv=False
    )

    # 2) Trip Patterns
    trip_df = trips if trips is not None else wtrips
    results["trip_patterns"] = run_clustering(
        "Trip Patterns", trip_df,
        numeric_like=["dist","distance","duration","time","speed","dep_hour","len","length","trav","trip"],
        categorical_like=["mode","purpose","weekday","daytype","region","area"],
        output_prefix="trip_patterns",
        add_trip_deriv=True
    )

    # 3) Education Journeys
    edu_df = etrips if etrips is not None else journey_edu
    results["education_journeys"] = run_clustering(
        "Education Journeys", edu_df,
        numeric_like=["dist","distance","duration","time","speed","dep_hour","age","len","length","trav","trip"],
        categorical_like=["mode","education","level","school","weekday","region","area"],
        output_prefix="education_journeys",
        add_trip_deriv=True
    )

    # 4) Regional Profiles
    regional_df = ptsum if ptsum is not None else master
    results["regional_profiles"] = run_clustering(
        "Regional Travel Profiles", regional_df,
        numeric_like=["avg","mean","income","age","trip","distance","duration","car","veh","count","freq"],
        categorical_like=["region","area","sex","gender"],
        output_prefix="regional_profiles",
        add_trip_deriv=False
    )

    # Save summary
    summary_path = os.path.join(OUT_DIR, "clustering_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSummary saved -> {os.path.relpath(summary_path)}")

    # 5) Joint Work vs Education (if both are present)
    print("\n===== Joint Clustering: Work vs Education =====")
    work = try_read("work_trips_processed.csv")
    edu = try_read("education_trips_processed.csv")
    if (work is not None) and (edu is not None):
        work["trip_type"] = "work"
        edu["trip_type"] = "education"
        joint = pd.concat([work, edu], ignore_index=True)

        # select numeric features
        patterns = ["dist", "distance", "dur", "duration", "time", "dep", "length", "speed", "trav", "trip"]
        cand = [c for c in joint.columns if any(p in c.lower() for p in patterns)]
        for c in cand:
            joint[c] = pd.to_numeric(joint[c], errors="coerce")
        num_cols = [c for c in cand if pd.api.types.is_numeric_dtype(joint[c])]

        X = joint[num_cols].replace([np.inf, -np.inf], np.nan).dropna()
        if X.empty:
            print("Joint: no usable rows after cleaning — skipping.")
        else:
            idx = X.index
            scaler = StandardScaler();
            Xs = scaler.fit_transform(X)

            best_score, best_k, best_labels = -1.0, None, None
            for k in range(2, 6):  # a bit smaller range for speed
                km = KMeans(n_clusters=k, n_init=10, random_state=42)
                labels = km.fit_predict(Xs)
                score = silhouette_score(Xs, labels)
                if score > best_score:
                    best_score, best_k, best_labels = score, k, labels

            joint["cluster"] = np.nan
            joint.loc[idx, "cluster"] = best_labels
            joint_csv = os.path.join(OUT_DIR, f"joint_work_edu_clusters_K{best_k}.csv")
            joint.to_csv(joint_csv, index=False)
            print(f"Joint clustering K={best_k} (silhouette={best_score:.3f}); saved -> {os.path.relpath(joint_csv)}")

            # plots
            joint_work_edu_plots(joint_csv)
    else:
        print("Skipping joint clustering — missing work or education dataset.")

    print("\n All analyses complete.")


if __name__ == "__main__":
    main()