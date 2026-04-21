"""
ml/recommender_v2.py
=====================
Enhanced ML recommendation engine — v2

New in v2:
  - Scope-specific recommendations (scope1/2/3 each get their own action)
  - Explainable AI (XAI) — human-readable reason for every recommendation
  - Priority colour system (HIGH=red, MEDIUM=orange, LOW=green)
  - Dominant scope detection
  - Top-3 de-duplicated recommendations
  - Graceful fallback when models not loaded
"""

import os
import json
import pickle
import warnings
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────

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

RECOMMENDATION_MESSAGES = {
    "switch_to_renewables":
        "Switch to renewable energy (solar/wind PPAs or rooftop solar) to cut Scope 2 emissions. Even 30% renewable procurement can reduce your grid footprint significantly.",
    "reduce_electricity_consumption":
        "Implement energy efficiency measures — LED lighting, smart HVAC scheduling, equipment power management, and an ISO 50001 energy audit.",
    "optimize_server_infrastructure":
        "Redesign your server layout to hot-aisle/cold-aisle containment or direct liquid cooling. Reducing PUE from 2.2 to 1.5 can cut data centre energy by ~30%.",
    "electrify_fleet_reduce_fuel":
        "Electrify company vehicles and switch diesel generators to grid+battery backup. Fuel combustion is your single largest Scope 1 driver.",
    "adopt_cloud_migration":
        "Migrate on-premise servers to a hyperscaler cloud. Cloud providers run at far higher utilisation rates and use greener energy than typical on-prem data centres.",
    "reduce_cloud_carbon":
        "Switch workloads to GCP (lowest carbon intensity) or purchase cloud carbon credits. Consider carbon-aware scheduling to run jobs during low-grid-intensity windows.",
    "improve_cooling_efficiency":
        "Your server cooling arrangement wastes significant energy. Move to hot-aisle/cold-aisle containment as a low-cost first step before considering liquid cooling.",
    "low_emission_maintain_practices":
        "Your emission profile is already low. Set science-based targets (SBTi), report under GHG Protocol, and consider net-zero commitments to stay ahead.",
    "reduce_scope3_purchases":
        "Audit purchased services spend and require sustainability disclosures from top suppliers. Scope 3 categories 1 and 11 are typically largest for service companies.",
    "hybrid_work_policy":
        "Implement a structured hybrid/remote work policy. Reducing office occupancy 2 days/week can cut electricity consumption by 20–30% without capital investment.",
}

PRIORITY_SCORES = {
    "switch_to_renewables": 9,
    "reduce_electricity_consumption": 8,
    "optimize_server_infrastructure": 6,
    "electrify_fleet_reduce_fuel": 9,
    "adopt_cloud_migration": 5,
    "reduce_cloud_carbon": 5,
    "improve_cooling_efficiency": 4,
    "low_emission_maintain_practices": 1,
    "reduce_scope3_purchases": 3,
    "hybrid_work_policy": 6,
}

PRIORITY_COLOUR = {
    9: {"level": "HIGH",   "colour": "#DC2626", "bg": "#FEF2F2", "label": "Critical"},
    8: {"level": "HIGH",   "colour": "#DC2626", "bg": "#FEF2F2", "label": "High"},
    7: {"level": "HIGH",   "colour": "#EA580C", "bg": "#FFF7ED", "label": "High"},
    6: {"level": "MEDIUM", "colour": "#D97706", "bg": "#FFFBEB", "label": "Medium"},
    5: {"level": "MEDIUM", "colour": "#D97706", "bg": "#FFFBEB", "label": "Medium"},
    4: {"level": "LOW",    "colour": "#16A34A", "bg": "#F0FDF4", "label": "Low"},
    3: {"level": "LOW",    "colour": "#16A34A", "bg": "#F0FDF4", "label": "Low"},
    2: {"level": "LOW",    "colour": "#16A34A", "bg": "#F0FDF4", "label": "Low"},
    1: {"level": "LOW",    "colour": "#16A34A", "bg": "#F0FDF4", "label": "Maintain"},
}

CLUSTER_DESCRIPTIONS = {
    0: "Fuel-Heavy Emitter — Scope 1 dominant. Fleet & combustion drives your footprint.",
    1: "Electricity-Heavy Emitter — Scope 2 dominant. Grid dependency is your main lever.",
    2: "Cloud & Services Emitter — Scope 3 dominant. Procurement and cloud choices matter.",
    3: "Low Emission Profile — Already performing well across all scopes.",
    4: "Infrastructure-Heavy Emitter — On-premise servers and data centre ops drive emissions.",
}

NUMERIC_FEATURES = [
    "num_employees", "electricity_kwh_per_month", "renewable_energy_percent",
    "diesel_litres_per_month", "petrol_litres_per_month", "natural_gas_m3_per_month",
    "server_rack_count", "num_servers_onprem", "num_laptops", "num_desktops",
    "cloud_monthly_bill_inr", "purchased_services_spend_inr_per_month",
    "server_area_sqft", "scope1_tco2e_monthly", "scope2_tco2e_monthly",
    "scope3_tco2e_monthly", "total_tco2e_monthly", "scope1_pct", "scope2_pct", "scope3_pct",
]

CATEGORICAL_FEATURES = [
    "industry_type", "company_size", "electricity_level",
    "server_arrangement", "cloud_provider",
]

# ─────────────────────────────────────────────────────────────
# SCOPE-SPECIFIC RECOMMENDATION LOGIC
# ─────────────────────────────────────────────────────────────

def _scope1_recommendation(data: Any, s1_pct: float) -> Dict:
    """Generate Scope 1 specific recommendation."""
    fuel = (_g(data,"diesel_litres_per_month",0) + _g(data,"petrol_litres_per_month",0))
    gas  = _g(data,"natural_gas_m3_per_month",0)
    generator = _g(data,"power_backup_runtime_hours",0)

    if s1_pct > 40 and fuel > 200:
        action = "Fleet electrification"
        detail = f"Your fleet burns ~{fuel:.0f} L/month — the single biggest Scope 1 source. Switch to EVs and eliminate this emission category entirely."
        priority = 9
    elif gas > 50:
        action = "Natural gas reduction"
        detail = f"Natural gas ({gas:.0f} m³/month) can be replaced with heat pumps or electric boilers. Target a 50% reduction in year 1."
        priority = 7
    elif generator > 20:
        action = "Generator phase-out"
        detail = f"Generator runtime of {generator:.0f} hrs/month contributes unnecessarily. Replace with UPS + grid battery systems."
        priority = 6
    elif s1_pct < 10:
        action = "Scope 1 is well managed"
        detail = "Your direct emissions are low. Maintain current practices and explore renewable gas certificates."
        priority = 1
    else:
        action = "Audit direct emission sources"
        detail = "Conduct a Scope 1 source audit. Focus on largest fuel consumers first — typically HVAC, vehicles, and backup generation."
        priority = 5

    return {
        "scope": "scope1",
        "action": action,
        "detail": detail,
        **_priority_meta(priority),
        "scope_pct": round(s1_pct, 1),
    }


def _scope2_recommendation(data: Any, s2_pct: float) -> Dict:
    """Generate Scope 2 specific recommendation."""
    kwh       = _g(data,"electricity_kwh_per_month",5000)
    renewable = _g(data,"renewable_energy_percent",0)
    racks     = _g(data,"server_rack_count",0)
    arrange   = _g(data,"server_arrangement","hot_aisle_cold_aisle")

    if renewable < 10 and kwh > 8000:
        action = "Procure renewable energy"
        detail = f"Only {renewable:.0f}% renewable with {kwh:,.0f} kWh/month consumption. A green tariff or solar PPA could eliminate 70-90% of Scope 2 immediately."
        priority = 9
    elif kwh > 15000:
        action = "Deep electricity efficiency programme"
        detail = f"At {kwh:,.0f} kWh/month you're in the top quartile of consumers. An ISO 50001 audit typically finds 15-25% savings."
        priority = 8
    elif racks > 10 and arrange == "stacked_high_density":
        action = "Data centre PUE improvement"
        detail = f"With {racks} racks in stacked-high-density arrangement, your PUE is likely ~2.2. Moving to hot-aisle/cold-aisle can drop it to ~1.5 — saving ~30% server energy."
        priority = 7
    elif renewable > 60:
        action = "Scope 2 is well managed"
        detail = f"At {renewable:.0f}% renewable energy you're leading the sector. Target 100% through additional PPAs or RECs."
        priority = 2
    else:
        action = "Increase renewable energy mix"
        detail = f"At {renewable:.0f}% renewable, there's room to grow. Start with a green tariff switch — often cost-neutral or cheaper in India's current market."
        priority = 6

    return {
        "scope": "scope2",
        "action": action,
        "detail": detail,
        **_priority_meta(priority),
        "scope_pct": round(s2_pct, 1),
    }


def _scope3_recommendation(data: Any, s3_pct: float) -> Dict:
    """Generate Scope 3 specific recommendation."""
    cloud_bill = _g(data,"cloud_monthly_bill_inr",0)
    provider   = _g(data,"cloud_provider","none")
    services   = _g(data,"purchased_services_spend_inr_per_month",0)
    onprem     = _g(data,"num_servers_onprem",0)

    if cloud_bill > 100000 and provider in ("aws","azure"):
        action = "Cloud carbon optimisation"
        detail = f"₹{cloud_bill:,.0f}/month on {provider.upper()} carries significant carbon. Switch to GCP (67% lower carbon) or enable carbon-aware compute scheduling."
        priority = 6
    elif onprem > 20 and cloud_bill < 10000:
        action = "Cloud migration strategy"
        detail = f"With {onprem} on-prem servers and minimal cloud spend, migration could reduce hardware lifecycle emissions by 40-60%."
        priority = 5
    elif services > 100000:
        action = "Sustainable procurement policy"
        detail = f"₹{services:,.0f}/month on purchased services. Require Scope 1+2 disclosure from your top 10 suppliers — they likely represent 80% of this footprint."
        priority = 5
    elif s3_pct < 20:
        action = "Scope 3 is well managed"
        detail = "Your value chain emissions are low relative to total footprint. Continue supplier engagement and consider a full Scope 3 inventory (GHG Protocol categories 1–15)."
        priority = 1
    else:
        action = "Scope 3 inventory & supplier engagement"
        detail = "Start with a full Scope 3 category assessment. Categories 1 (purchased goods), 11 (use of sold products), and 15 (investments) are typically largest."
        priority = 4

    return {
        "scope": "scope3",
        "action": action,
        "detail": detail,
        **_priority_meta(priority),
        "scope_pct": round(s3_pct, 1),
    }


def _priority_meta(score: int) -> Dict:
    meta = PRIORITY_COLOUR.get(score, PRIORITY_COLOUR[4])
    return {
        "priority_score": score,
        "priority_level": meta["level"],
        "priority_colour": meta["colour"],
        "priority_bg": meta["bg"],
        "priority_label": meta["label"],
    }


# ─────────────────────────────────────────────────────────────
# EXPLAINABLE AI  (XAI)
# ─────────────────────────────────────────────────────────────

def _generate_explanation(rec_name: str, data: Any, s1_pct: float, s2_pct: float, s3_pct: float) -> str:
    """Generate a human-readable reason for why this recommendation was chosen."""
    kwh      = _g(data,"electricity_kwh_per_month",0)
    renewable= _g(data,"renewable_energy_percent",0)
    fuel     = _g(data,"diesel_litres_per_month",0) + _g(data,"petrol_litres_per_month",0)
    racks    = _g(data,"server_rack_count",0)
    cloud    = _g(data,"cloud_monthly_bill_inr",0)
    services = _g(data,"purchased_services_spend_inr_per_month",0)
    employees= _g(data,"num_employees",50)
    arrange  = _g(data,"server_arrangement","hot_aisle_cold_aisle")

    reasons = {
        "switch_to_renewables": f"High electricity consumption ({kwh:,.0f} kWh/month) combined with low renewable energy usage ({renewable:.0f}%) makes grid procurement the fastest lever to cut Scope 2.",
        "reduce_electricity_consumption": f"Electricity at {kwh:,.0f} kWh/month places you in the high-consumption tier. This drives {s2_pct:.0f}% of total emissions — efficiency measures have the highest ROI here.",
        "optimize_server_infrastructure": f"You have {racks} server racks in '{arrange}' arrangement. Suboptimal cooling layout inflates PUE and adds unnecessary Scope 2 load.",
        "electrify_fleet_reduce_fuel": f"Fuel usage ({fuel:.0f} L/month) accounts for {s1_pct:.0f}% of your total emissions. This is your dominant Scope 1 source.",
        "adopt_cloud_migration": f"High on-premise server count with low cloud spend suggests migration potential. Cloud hyperscalers run at 3–4× higher utilisation efficiency.",
        "reduce_cloud_carbon": f"Cloud spend of ₹{cloud:,.0f}/month on a carbon-intensive provider contributes meaningfully to Scope 3. Provider switching is low-effort, high-impact.",
        "improve_cooling_efficiency": f"Server arrangement ({arrange}) and {racks} racks indicate cooling inefficiency. PUE improvements reduce Scope 2 without any change in workload.",
        "low_emission_maintain_practices": f"All scope percentages are balanced and total emissions are low. You are already in the top-performing tier for your industry.",
        "reduce_scope3_purchases": f"Purchased services at ₹{services:,.0f}/month drive {s3_pct:.0f}% of total emissions. Supplier engagement is the primary Scope 3 lever.",
        "hybrid_work_policy": f"With {employees} employees and {kwh:,.0f} kWh/month, per-capita electricity is high. Hybrid work can reduce office load without capital investment.",
    }
    return reasons.get(rec_name, "Based on your emissions profile, this action offers the best reduction potential.")


def _dominant_scope(s1_pct, s2_pct, s3_pct) -> Dict:
    """Return info about the dominant emission scope."""
    scopes = [
        {"scope": "Scope 1", "key": "scope1", "pct": s1_pct,
         "description": "Direct combustion (fuel, generators)",
         "colour": "#DC2626", "bg": "#FEF2F2"},
        {"scope": "Scope 2", "key": "scope2", "pct": s2_pct,
         "description": "Electricity & purchased energy",
         "colour": "#D97706", "bg": "#FFFBEB"},
        {"scope": "Scope 3", "key": "scope3", "pct": s3_pct,
         "description": "Value chain, cloud & services",
         "colour": "#2563EB", "bg": "#EFF6FF"},
    ]
    dominant = max(scopes, key=lambda x: x["pct"])
    return dominant


def _g(obj, attr, default=0):
    v = getattr(obj, attr, default)
    return v if v is not None else default


# ─────────────────────────────────────────────────────────────
# MAIN RECOMMENDER CLASS
# ─────────────────────────────────────────────────────────────

class CarbonMLRecommenderV2:
    def __init__(self, models_dir: str = None):
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), "models")
        self.models_dir = models_dir
        self._loaded = False
        self._dt = self._km = self._scaler = self._le_dict = self._meta = None
        try:
            self._load_models()
            self._loaded = True
        except Exception as e:
            print(f"⚠️  ML models not found ({e}). Rule-based fallback active.")

    def _load_models(self):
        def _load(name):
            with open(os.path.join(self.models_dir, f"{name}.pkl"), "rb") as f:
                return pickle.load(f)
        self._dt     = _load("decision_tree")
        self._km     = _load("kmeans")
        self._scaler = _load("scaler")
        self._le_dict= _load("label_encoders")
        with open(os.path.join(self.models_dir, "model_metadata.json")) as f:
            self._meta = json.load(f)

    @staticmethod
    def _electricity_level(kwh):
        if kwh < 3000:  return "low"
        if kwh < 8000:  return "medium"
        if kwh < 15000: return "high"
        return "very_high"

    @staticmethod
    def _company_size(emp):
        if emp <= 50:  return "small"
        if emp <= 300: return "medium"
        return "large"

    def _build_feature_row(self, result, data):
        monthly   = result.get("monthly", {})
        scope_pct = result.get("scope_percentages", {})
        total_m   = monthly.get("total_tco2e", 0.001) or 0.001

        row = {
            "num_employees":             _g(data,"num_employees",50),
            "electricity_kwh_per_month": _g(data,"electricity_kwh_per_month",5000),
            "renewable_energy_percent":  _g(data,"renewable_energy_percent",0),
            "diesel_litres_per_month":   _g(data,"diesel_litres_per_month",0),
            "petrol_litres_per_month":   _g(data,"petrol_litres_per_month",0),
            "natural_gas_m3_per_month":  _g(data,"natural_gas_m3_per_month",0),
            "server_rack_count":         _g(data,"server_rack_count",0),
            "num_servers_onprem":        _g(data,"num_servers_onprem",0),
            "num_laptops":               _g(data,"num_laptops",0),
            "num_desktops":              _g(data,"num_desktops",0),
            "cloud_monthly_bill_inr":    _g(data,"cloud_monthly_bill_inr",0),
            "purchased_services_spend_inr_per_month": _g(data,"purchased_services_spend_inr_per_month",0),
            "server_area_sqft":          _g(data,"server_area_sqft",0),
            "scope1_tco2e_monthly": monthly.get("scope1_tco2e",0),
            "scope2_tco2e_monthly": monthly.get("scope2_tco2e",0),
            "scope3_tco2e_monthly": monthly.get("scope3_tco2e",0),
            "total_tco2e_monthly":  total_m,
            "scope1_pct": scope_pct.get("scope1",0),
            "scope2_pct": scope_pct.get("scope2",0),
            "scope3_pct": scope_pct.get("scope3",0),
        }
        for col in CATEGORICAL_FEATURES:
            val_map = {
                "industry_type":     _g(data,"industry_type","IT"),
                "company_size":      self._company_size(_g(data,"num_employees",50)),
                "electricity_level": self._electricity_level(_g(data,"electricity_kwh_per_month",5000)),
                "server_arrangement":_g(data,"server_arrangement","hot_aisle_cold_aisle"),
                "cloud_provider":    _g(data,"cloud_provider","none"),
            }
            le = self._le_dict.get(col)
            if le:
                try:   row[col+"_enc"] = int(le.transform([str(val_map[col])])[0])
                except: row[col+"_enc"] = 0

        feature_cols = self._meta["feature_columns"]
        return pd.DataFrame([{c: row.get(c, 0) for c in feature_cols}])

    def recommend(self, result: Dict, data: Any, rule_findings=None) -> Dict:
        scope_pct = result.get("scope_percentages", {})
        s1p = scope_pct.get("scope1", 33.3)
        s2p = scope_pct.get("scope2", 33.3)
        s3p = scope_pct.get("scope3", 33.3)

        # Scope-specific recommendations (always computed, no ML needed)
        scope_recs = {
            "scope1": _scope1_recommendation(data, s1p),
            "scope2": _scope2_recommendation(data, s2p),
            "scope3": _scope3_recommendation(data, s3p),
        }

        dominant = _dominant_scope(s1p, s2p, s3p)

        if not self._loaded:
            return self._fallback(rule_findings, scope_recs, dominant)

        try:
            X_row = self._build_feature_row(result, data)

            # Append K-Means cluster as 26th feature (hybrid model expects it)
            X_scaled = self._scaler.transform(X_row)
            cluster  = int(self._km.predict(X_scaled)[0])
            cluster_col = pd.DataFrame([[cluster]], columns=["kmeans_cluster"])
            X_row_hybrid = pd.concat([X_row.reset_index(drop=True), cluster_col], axis=1)

            # Decision Tree (hybrid)
            label  = int(self._dt.predict(X_row_hybrid)[0])
            proba  = self._dt.predict_proba(X_row_hybrid)[0]
            classes = list(self._dt.classes_)
            idx = classes.index(label)
            conf = float(proba[idx]) * 100
            conf = min(95, max(15, conf))

            # Top-3 unique recommendations
            top3_idx = np.argsort(proba)[::-1]
            seen_cats = set()
            top3 = []
            for i in top3_idx:
                if proba[i] < 0.01: continue
                name = RECOMMENDATION_NAMES[i]
                if name in seen_cats: continue
                seen_cats.add(name)
                ps = PRIORITY_SCORES[name]
                top3.append({
                    "rank": len(top3) + 1,
                    "recommendation": name,
                    "message": RECOMMENDATION_MESSAGES[name],
                    "confidence": round(float(proba[i]) * 100, 1),
                    **_priority_meta(ps),
                    "explanation": _generate_explanation(name, data, s1p, s2p, s3p),
                    "is_primary": len(top3) == 0,
                })
                if (len(top3) == 10): break

            # K-Means cluster
            X_scaled = self._scaler.transform(X_row)
            cluster  = int(self._km.predict(X_scaled)[0])

            primary_name = RECOMMENDATION_NAMES[idx]
            primary_ps   = PRIORITY_SCORES[primary_name]

            return {
                "ml_available": True,
                "ml_primary_recommendation": primary_name,
                "ml_primary_message": RECOMMENDATION_MESSAGES[primary_name],
                "ml_confidence": round(conf, 1),
                **{f"ml_{k}": v for k, v in _priority_meta(primary_ps).items()},
                "ml_explanation": _generate_explanation(primary_name, data, s1p, s2p, s3p),
                "ml_top3_recommendations": top3,
                "ml_cluster": cluster,
                "ml_cluster_description": CLUSTER_DESCRIPTIONS.get(cluster, f"Cluster {cluster}"),
                "ml_dominant_scope": dominant,
                "ml_scope_recommendations": scope_recs,
                "ml_enhanced_findings": self._merge_findings(rule_findings, top3),
            }

        except Exception as e:
            print(f"⚠️  ML inference error: {e}")
            return self._fallback(rule_findings, scope_recs, dominant)

    def _merge_findings(self, rule_findings, ml_top3):
        merged = []
        seen = set()
        for rec in ml_top3:
            cat = rec["recommendation"]
            if cat not in seen:
                merged.append({
                    "source": "ML",
                    "severity": rec["priority_level"],
                    "priority_colour": rec["priority_colour"],
                    "priority_bg": rec["priority_bg"],
                    "priority_label": rec["priority_label"],
                    "category": cat,
                    "message": rec["message"],
                    "explanation": rec["explanation"],
                    "confidence": rec["confidence"],
                    "priority_score": rec["priority_score"],
                    "is_primary": rec["is_primary"],
                })
                seen.add(cat)
        if rule_findings:
            for f in rule_findings:
                cat = getattr(f,"category","")
                if cat not in seen:
                    sev = getattr(f,"severity",None)
                    sev_name = sev.name if hasattr(sev,"name") else str(sev)
                    merged.append({
                        "source": "Rules",
                        "severity": sev_name,
                        "priority_colour": "#6B7280",
                        "priority_bg": "#F9FAFB",
                        "priority_label": sev_name.title(),
                        "category": cat,
                        "message": getattr(f,"message",""),
                        "recommendation": getattr(f,"recommendation",""),
                        "explanation": None,
                        "confidence": None,
                        "priority_score": None,
                        "is_primary": False,
                    })
                    seen.add(cat)
        merged.sort(key=lambda x: (
            0 if x["source"]=="ML" else 1,
            {"HIGH":0,"MEDIUM":1,"LOW":2}.get(x.get("severity","LOW"),2),
            -(x.get("priority_score") or 0),
        ))
        return merged

    def _fallback(self, rule_findings, scope_recs, dominant):
        findings = []
        if rule_findings:
            for f in rule_findings:
                sev = getattr(f,"severity",None)
                findings.append({
                    "source": "Rules",
                    "severity": sev.name if hasattr(sev,"name") else "INFO",
                    "category": getattr(f,"category",""),
                    "message": getattr(f,"message",""),
                    "is_primary": False,
                })
        return {
            "ml_available": False,
            "ml_primary_recommendation": None,
            "ml_primary_message": "ML models not loaded — using rule-based recommendations.",
            "ml_confidence": 0,
            "ml_priority_level": "LOW",
            "ml_priority_colour": "#16A34A",
            "ml_priority_bg": "#F0FDF4",
            "ml_priority_label": "Info",
            "ml_priority_score": 0,
            "ml_explanation": None,
            "ml_top3_recommendations": [],
            "ml_cluster": None,
            "ml_cluster_description": "Cluster analysis unavailable.",
            "ml_dominant_scope": dominant,
            "ml_scope_recommendations": scope_recs,
            "ml_enhanced_findings": findings,
        }


_instance = None
def get_recommender_v2(models_dir=None):
    global _instance
    if _instance is None:
        _instance = CarbonMLRecommenderV2(models_dir=models_dir)
    return _instance
