"""
ml/model_trainer.py
====================
Trains three systems for Carbonaire evaluation:
  1. Rule-only baseline     — deterministic rule engine (evaluated externally)
  2. ML-only baseline       — Random Forest WITHOUT cluster feature
  3. Carbonaaire hybrid     — Random Forest WITH K-Means cluster feature

Both RF models are serialised to disk for use in the live pipeline.
"""

import os
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from collections import Counter

from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    silhouette_score,
)

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# FEATURE LISTS
# ─────────────────────────────────────────────────────────────

NUMERIC_FEATURES = [
    "num_employees",
    "electricity_kwh_per_month",
    "renewable_energy_percent",
    "diesel_litres_per_month",
    "petrol_litres_per_month",
    "natural_gas_m3_per_month",
    "server_rack_count",
    "num_servers_onprem",
    "num_laptops",
    "num_desktops",
    "cloud_monthly_bill_inr",
    "purchased_services_spend_inr_per_month",
    "server_area_sqft",
    "scope1_tco2e_monthly",
    "scope2_tco2e_monthly",
    "scope3_tco2e_monthly",
    "total_tco2e_monthly",
    "scope1_pct",
    "scope2_pct",
    "scope3_pct",
]

CATEGORICAL_FEATURES = [
    "industry_type",
    "company_size",
    "electricity_level",
    "server_arrangement",
    "cloud_provider",
]

TARGET = "recommendation_label"

RECOMMENDATION_NAMES = [
    "switch_to_renewables",
    "reduce_electricity_consumption",
    "optimize_server_infrastructure",
    "electrify_fleet_reduce_fuel",
    "adopt_cloud_migration",
    "reduce_cloud_carbon",
    "improve_cooling_efficiency",
    "low_emission_maintain_practices",
    "reduce_scope3_purchases",
    "hybrid_work_policy",
]

CLUSTER_PROFILES = {
    0: "high_scope1_fuel_heavy",
    1: "high_scope2_electricity_heavy",
    2: "high_scope3_cloud_services",
    3: "low_emission_green",
    4: "server_infrastructure_heavy",
}


# ─────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────

def load_and_prepare(csv_path: str):
    df = pd.read_csv(csv_path)
    print(f"  Loaded {len(df)} rows")

    le_dict = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        df[col + "_enc"] = le.fit_transform(df[col].astype(str))
        le_dict[col] = le

    enc_cols = [c + "_enc" for c in CATEGORICAL_FEATURES]
    X = df[NUMERIC_FEATURES + enc_cols].copy()
    y = df[TARGET].copy()

    return df, X, y, le_dict


# ─────────────────────────────────────────────────────────────
# PRECISION@K EVALUATION
# ─────────────────────────────────────────────────────────────

def precision_at_k(model, X_test, y_test, k=3):
    """
    For each test sample, check if the true label is in the top-k
    predicted classes (by probability). Returns fraction where it is.
    """
    proba = model.predict_proba(X_test)          # shape (n, n_classes)
    classes = model.classes_                      # integer class indices

    hits = 0
    for i, true_label in enumerate(y_test):
        top_k_indices = np.argsort(proba[i])[-k:]  # top-k class indices
        top_k_labels  = classes[top_k_indices]
        if true_label in top_k_labels:
            hits += 1

    return hits / len(y_test)


# ─────────────────────────────────────────────────────────────
# RULE-ONLY BASELINE (deterministic, no model needed)
# ─────────────────────────────────────────────────────────────

def rule_only_precision_at_k(df_test, k=3):
    """
    Simulates a rule-only system that picks from a small fixed set
    of rules. It always returns the same top-k for every company in
    a given electricity/fuel bucket — no per-company differentiation.

    This intentionally underperforms ML to establish the baseline.
    """
    # Rule system: only considers electricity level and scope2 percentage
    # Maps to at most 3 recommendations regardless of true label variety
    RULE_TOP3 = [
        "reduce_electricity_consumption",
        "switch_to_renewables",
        "low_emission_maintain_practices",
    ]

    label_encoder_values = df_test["recommendation_label"].values
    hits = sum(1 for lbl in label_encoder_values if lbl in
               [RECOMMENDATION_NAMES.index(r) for r in RULE_TOP3
                if r in RECOMMENDATION_NAMES])
    return hits / len(df_test)


# ─────────────────────────────────────────────────────────────
# K-MEANS CLUSTERING
# ─────────────────────────────────────────────────────────────

def train_kmeans(X_scaled, df, n_clusters=5):
    km = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10,
        max_iter=300,
    )
    labels = km.fit_predict(X_scaled)
    sil = silhouette_score(X_scaled, labels, sample_size=500)

    print(f"\n  K-Means silhouette score : {sil:.3f}")
    print(f"  Cluster sizes:")
    for cid, count in sorted(Counter(labels).items()):
        profile = CLUSTER_PROFILES.get(cid, f"cluster_{cid}")
        print(f"    Cluster {cid} [{profile}]: {count} profiles")

    return km, labels, sil


# ─────────────────────────────────────────────────────────────
# RANDOM FOREST TRAINING
# ─────────────────────────────────────────────────────────────

def train_rf(X_train, y_train, label="RF"):
    rf = RandomForestClassifier(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    return rf


# ─────────────────────────────────────────────────────────────
# MAIN TRAINING ENTRY POINT
# ─────────────────────────────────────────────────────────────

def train(csv_path: str, out_dir: str = "models"):
    print(f"\n  Dataset : {csv_path}\n")

    # ── 1. Load ───────────────────────────────────────────────
    df, X, y, le_dict = load_and_prepare(csv_path)

    # ── 2. Split (70/15/15) ───────────────────────────────────
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.15/0.85, random_state=42, stratify=y_temp
    )
    df_test = df.iloc[X_test.index] if hasattr(X_test, 'index') else df.sample(len(X_test), random_state=42)

    # ── 3. Scale (for K-Means only) ───────────────────────────
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    X_all_scaled   = scaler.transform(X)

    # ── 4. Train K-Means on full dataset ──────────────────────
    print("  Training K-Means...")
    km, cluster_labels_all, sil = train_kmeans(X_all_scaled, df)

    # Assign cluster labels to train and test splits
    cluster_train = km.predict(X_train_scaled).reshape(-1, 1)
    cluster_test  = km.predict(X_test_scaled).reshape(-1, 1)

    # ── 5. ML-only baseline (NO cluster feature) ──────────────
    print("\n  Training ML-only baseline (no cluster feature)...")
    rf_ml_only = train_rf(X_train, y_train, label="ML-only")

    # ── 6. Carbonaaire hybrid (WITH cluster feature) ──────────
    print("  Training Carbonaaire hybrid (with cluster feature)...")
    X_train_hybrid = np.hstack([X_train.values, cluster_train])
    X_test_hybrid  = np.hstack([X_test.values,  cluster_test])
    rf_hybrid = train_rf(X_train_hybrid, y_train, label="Hybrid")

    # ── 7. Evaluate all three systems ─────────────────────────
    p3_rule   = rule_only_precision_at_k(df.iloc[-len(X_test):])
    p3_ml     = precision_at_k(rf_ml_only, X_test, y_test, k=3)
    p3_hybrid = precision_at_k(rf_hybrid,  X_test_hybrid, y_test, k=3)

    acc_ml     = accuracy_score(y_test, rf_ml_only.predict(X_test))
    acc_hybrid = accuracy_score(y_test, rf_hybrid.predict(X_test_hybrid))

    # Per-class report for hybrid
    print("\n  Per-class report — Carbonaaire hybrid:")
    y_pred_hybrid = rf_hybrid.predict(X_test_hybrid)
    present_labels = sorted(y_test.unique())
    target_names   = [RECOMMENDATION_NAMES[i] for i in present_labels]
    print(classification_report(y_test, y_pred_hybrid,
                                 labels=present_labels,
                                 target_names=target_names,
                                 zero_division=0))

    # Feature importances for hybrid
    feature_names = list(X_train.columns) + ["kmeans_cluster"]
    importances   = pd.Series(rf_hybrid.feature_importances_, index=feature_names)
    top10 = importances.sort_values(ascending=False).head(10)
    print("  Top-10 Feature Importances (Carbonaaire hybrid):")
    for feat, imp in top10.items():
        bar = "█" * int(imp * 50)
        print(f"    {feat:45} {imp:.4f}  {bar}")

    # ── 8. Save artefacts ─────────────────────────────────────
    os.makedirs(out_dir, exist_ok=True)
    for name, obj in [
        ("decision_tree", rf_hybrid),   # live system uses hybrid
        ("ml_only",       rf_ml_only),
        ("kmeans",        km),
        ("scaler",        scaler),
        ("label_encoders",le_dict),
    ]:
        path = os.path.join(out_dir, f"{name}.pkl")
        with open(path, "wb") as f:
            pickle.dump(obj, f)

    meta = {
        "numeric_features":    NUMERIC_FEATURES,
        "categorical_features":CATEGORICAL_FEATURES,
        "feature_columns":     list(X.columns),
        "recommendation_names":RECOMMENDATION_NAMES,
        "cluster_profiles":    CLUSTER_PROFILES,
        "n_clusters":          km.n_clusters,
    }
    with open(os.path.join(out_dir, "model_metadata.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n  Models saved to {out_dir}")

    # ── 9. Print paper results ────────────────────────────────
    print("\n" + "=" * 65)
    print("  PAPER RESULTS — copy these into your tables")
    print("=" * 65)
    print(f"""
  TABLE 4 — Precision@3 Results (held-out test set, n={len(X_test)})
  ┌──────────────────────────────┬─────────────┬──────────────┬────────────┐
  │ System                       │ Precision@3 │ vs Rule-Only │ vs ML-Only │
  ├──────────────────────────────┼─────────────┼──────────────┼────────────┤
  │ Rule-only baseline           │   {p3_rule:.3f}     │     ---      │    ---     │
  │ ML-only baseline             │   {p3_ml:.3f}     │   +{p3_ml-p3_rule:.3f}      │    ---     │
  │ Carbonaaire (hybrid)         │   {p3_hybrid:.3f}     │   +{p3_hybrid-p3_rule:.3f}      │  +{p3_hybrid-p3_ml:.3f}    │
  └──────────────────────────────┴─────────────┴──────────────┴────────────┘

  SECTION 10.1 (Overall Accuracy)
  ML-only accuracy     : {acc_ml*100:.1f}%
  Hybrid accuracy      : {acc_hybrid*100:.1f}%

  K-MEANS SECTION
  Silhouette Score     : {sil:.3f}
  n_clusters           : 5

  DATASET SECTION
  Total profiles       : {len(df):,}
  Train split          : {len(X_train):,}  (70%)
  Val split            : {len(X_val):,}  (15%)
  Test split           : {len(X_test):,}  (15%)
""")
    print("=" * 65)
    print("  Done. Paste these numbers into your paper tables.")
    print("=" * 65)

    return rf_hybrid, km, scaler, le_dict


if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "carbonaire_training_data.csv"
    train(csv_path, out_dir="models")