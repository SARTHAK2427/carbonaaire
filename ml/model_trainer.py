"""
ml/model_trainer.py
====================
Trains two complementary models for Carbonaire:
  1. DecisionTreeClassifier  — predicts the best recommendation label
  2. KMeans                  — clusters companies into emission profiles

Both models are serialised to disk for use in the live pipeline.
"""

import os
import json
import pickle
import warnings
import numpy as np
import pandas as pd
from collections import Counter

from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report, confusion_matrix,
    accuracy_score, silhouette_score,
)
from sklearn.pipeline import Pipeline

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# FEATURE ENGINEERING
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


def load_and_prepare(csv_path: str):
    """Load CSV and engineer features."""
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"Class distribution:\n{df['primary_recommendation'].value_counts().to_string()}\n")

    # One-hot encode categoricals
    le_dict = {}
    for col in CATEGORICAL_FEATURES:
        le = LabelEncoder()
        df[col + "_enc"] = le.fit_transform(df[col].astype(str))
        le_dict[col] = le

    # Feature matrix
    enc_cols = [c + "_enc" for c in CATEGORICAL_FEATURES]
    X = df[NUMERIC_FEATURES + enc_cols].copy()
    y = df[TARGET].copy()

    return df, X, y, le_dict


# ─────────────────────────────────────────────────────────────
# DECISION TREE CLASSIFIER
# ─────────────────────────────────────────────────────────────

def train_decision_tree(X_train, y_train, X_test, y_test):
    """
    Train an interpretable Decision Tree.

    Why Decision Tree?
    - Fully interpretable — we can see exactly why a recommendation was made
    - Fast inference (< 1ms per prediction)
    - Handles mixed feature types well
    - max_depth=8 keeps it lean and avoids overfitting
    - No feature scaling needed
    """

    dt = RandomForestClassifier(

        n_estimators=100,
        max_depth=10,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=42,
    )
    

    dt.fit(X_train, y_train)

    y_pred = dt.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("=" * 60)
    print("DECISION TREE CLASSIFIER")
    print("=" * 60)
    print(f"Test Accuracy  : {acc:.3f} ({acc*100:.1f}%)")

    # Cross-validation
    cv_scores = cross_val_score(dt, X_train, y_train, cv=5, scoring="accuracy")
    print(f"5-Fold CV Mean : {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    print("\nClassification Report:")
    present_labels = sorted(y_test.unique())
    target_names = [RECOMMENDATION_NAMES[i] for i in present_labels]
    print(classification_report(y_test, y_pred, labels=present_labels, target_names=target_names, zero_division=0))

    # Feature importance
    feature_names = X_train.columns.tolist()
    importances = pd.Series(dt.feature_importances_, index=feature_names)
    top10 = importances.sort_values(ascending=False).head(10)
    print("Top-10 Feature Importances:")
    for feat, imp in top10.items():
        bar = "█" * int(imp * 50)
        print(f"  {feat:45} {imp:.4f}  {bar}")

    return dt, acc


# ─────────────────────────────────────────────────────────────
# K-MEANS CLUSTERING
# ─────────────────────────────────────────────────────────────

def train_kmeans(X_scaled, df, n_clusters=5):
    """
    Train K-Means for company segmentation.

    Why K-Means?
    - Groups similar companies together → cluster-level recommendations
    - Finds natural emission patterns in the data
    - Useful for dashboard visualisation and peer benchmarking
    - n_clusters=5 maps to 5 emission archetypes
    """
    km = KMeans(
        n_clusters=n_clusters,
        random_state=42,
        n_init=10,
        max_iter=300,
    )
    labels = km.fit_predict(X_scaled)

    sil = silhouette_score(X_scaled, labels, sample_size=500)
    inertia = km.inertia_

    print("\n" + "=" * 60)
    print("K-MEANS CLUSTERING")
    print("=" * 60)
    print(f"Silhouette Score : {sil:.3f}  (0=bad, 1=perfect)")
    print(f"Inertia          : {inertia:.1f}")
    print(f"\nCluster sizes:")
    for cid, count in sorted(Counter(labels).items()):
        bar = "█" * int(count / 5)
        print(f"  Cluster {cid}: {count:4d} companies  {bar}")

    # Describe each cluster
    df_c = df.copy()
    df_c["cluster"] = labels
    print("\nCluster Profiles (mean values):")
    cluster_summary = df_c.groupby("cluster")[[
        "scope1_pct", "scope2_pct", "scope3_pct",
        "total_tco2e_monthly", "renewable_energy_percent",
        "electricity_kwh_per_month", "diesel_litres_per_month",
    ]].mean().round(2)
    print(cluster_summary.to_string())

    # Dominant recommendation per cluster
    print("\nDominant Recommendation per Cluster:")
    for cid in range(n_clusters):
        cluster_recs = df_c[df_c["cluster"] == cid]["primary_recommendation"]
        dominant = cluster_recs.mode()[0]
        profile  = CLUSTER_PROFILES.get(cid, f"cluster_{cid}")
        print(f"  Cluster {cid} [{profile:30}] → {dominant}")

    return km, labels, sil


# ─────────────────────────────────────────────────────────────
# SAVE ARTEFACTS
# ─────────────────────────────────────────────────────────────

def save_model_artifacts(dt, km, scaler, le_dict, X_columns, out_dir: str):
    """Serialise all model artefacts to disk."""
    os.makedirs(out_dir, exist_ok=True)

    artefacts = {
        "decision_tree": dt,
        "kmeans": km,
        "scaler": scaler,
        "label_encoders": le_dict,
    }
    for name, obj in artefacts.items():
        path = os.path.join(out_dir, f"{name}.pkl")
        with open(path, "wb") as f:
            pickle.dump(obj, f)
        print(f"  Saved: {path}")

    # Save metadata
    meta = {
        "numeric_features": NUMERIC_FEATURES,
        "categorical_features": CATEGORICAL_FEATURES,
        "feature_columns": list(X_columns),
        "recommendation_names": RECOMMENDATION_NAMES,
        "cluster_profiles": CLUSTER_PROFILES,
        "n_clusters": km.n_clusters,
    }
    meta_path = os.path.join(out_dir, "model_metadata.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  Saved: {meta_path}")


# ─────────────────────────────────────────────────────────────
# MAIN TRAINING ENTRY POINT
# ─────────────────────────────────────────────────────────────

def train(csv_path: str, out_dir: str = "models"):
    print(f"\n🌿  CARBONAIRE — ML Model Training")
    print(f"    Dataset : {csv_path}")
    print(f"    Output  : {out_dir}\n")

    # 1. Load data
    df, X, y, le_dict = load_and_prepare(csv_path)

    # 2. Train/test split
    # Only stratify if all classes have >= 2 members
    from collections import Counter
    counts = Counter(y)
    can_stratify = all(v >= 2 for v in counts.values())
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42,
        stratify=y if can_stratify else None
    )

    # 3. Scale features (for K-Means only — DT doesn't need scaling)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)
    X_all_scaled   = scaler.transform(X)

    # 4. Train Decision Tree
    dt, dt_acc = train_decision_tree(X_train, y_train, X_test, y_test)

    # 5. Train K-Means on full dataset
    km, cluster_labels, sil = train_kmeans(X_all_scaled, df)

    # 6. Save everything
    print(f"\n💾  Saving model artefacts to '{out_dir}/'...")
    save_model_artifacts(dt, km, scaler, le_dict, X.columns, out_dir)

    print(f"\n✅  Training complete!")
    print(f"    DT Accuracy      : {dt_acc:.1%}")
    print(f"    KMeans Silhouette: {sil:.3f}")

    return dt, km, scaler, le_dict


if __name__ == "__main__":
    import sys
    csv_path = sys.argv[1] if len(sys.argv) > 1 else "carbonaire_training_data.csv"
    train(csv_path, out_dir="models")
