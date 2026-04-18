"""
ml/run_training.py
==================
End-to-end script:
  1. Generate synthetic dataset (500 profiles)
  2. Train Decision Tree + K-Means
  3. Save all model artefacts to ml/models/
  4. Print a sample prediction to verify integration

Run from the carbonaire root directory:
    python ml/run_training.py
"""

import os
import sys

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.dataset_generator import generate_dataset, save_dataset, RECOMMENDATIONS
from ml.model_trainer import train

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
DATA_DIR   = os.path.join(os.path.dirname(__file__), "data")


def main():
    print("=" * 65)
    print("  CARBONAIRE — ML Training Pipeline")
    print("=" * 65)

    # ── Step 1: Generate dataset ──────────────────────────────
    print("\n[1/3] Generating synthetic training dataset (500 profiles)...")
    dataset = generate_dataset(500)
    csv_path, json_path = save_dataset(dataset, out_dir=DATA_DIR)

    # ── Step 2: Train models ──────────────────────────────────
    print("\n[2/3] Training models...")
    dt, km, scaler, le_dict = train(csv_path, out_dir=MODELS_DIR)

    # ── Step 3: Verify with a sample prediction ───────────────
    print("\n[3/3] Smoke test — sample inference...")
    from ml.recommender import CarbonMLRecommender

    rec = CarbonMLRecommender(models_dir=MODELS_DIR)

    # Simulate a pipeline result for a mid-sized IT company
    mock_result = {
        "monthly": {
            "total_tco2e": 12.4,
            "scope1_tco2e": 1.1,
            "scope2_tco2e": 9.5,
            "scope3_tco2e": 1.8,
        },
        "annual": {"total_tco2e": 148.8},
        "scope_percentages": {
            "scope1": 8.9, "scope2": 76.6, "scope3": 14.5
        },
    }

    class MockData:
        company_name = "TechNova Solutions"
        industry_type = "IT/ITES"
        num_employees = 120
        electricity_kwh_per_month = 14000
        renewable_energy_percent = 5.0
        diesel_litres_per_month = 30.0
        petrol_litres_per_month = 10.0
        natural_gas_m3_per_month = 0.0
        server_rack_count = 8
        num_servers_onprem = 12
        num_laptops = 100
        num_desktops = 20
        server_arrangement = "hot_aisle_cold_aisle"
        server_area_sqft = 320.0
        cloud_provider = "aws"
        cloud_monthly_bill_inr = 45000.0
        purchased_services_spend_inr_per_month = 30000.0
        annual_revenue_inr_cr = 8.5

    output = rec.recommend(mock_result, MockData())

    print(f"\n  ML Available           : {output['ml_available']}")
    print(f"  Primary Recommendation : {output['ml_primary_recommendation']}")
    print(f"  Confidence             : {output['ml_confidence']:.1f}%")
    print(f"  Priority Score         : {output['ml_priority_score']}/10")
    print(f"  Cluster                : {output['ml_cluster']} — {output['ml_cluster_description']}")
    print(f"\n  Top-3 Recommendations:")
    for i, r in enumerate(output["ml_top3_recommendations"], 1):
        print(f"    {i}. {r['recommendation']:40} ({r['confidence']:.1f}% confidence)")

    print(f"\n  ML Message: {output['ml_primary_message']}")

    print("\n" + "=" * 65)
    print("  ✅  All done! Models ready in ml/models/")
    print("=" * 65)
    print("""
  Integration:
    In api_server.py, add:
      from ml.recommender import get_recommender
      recommender = get_recommender()

    In your /api/run endpoint, after RuleEngine:
      ml_output = recommender.recommend(result, data, findings)
      return { ..., "ml": ml_output }
""")


if __name__ == "__main__":
    main()
