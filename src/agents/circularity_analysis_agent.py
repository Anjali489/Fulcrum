from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Dict, Tuple, Optional

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

# GCS config
GCS_RESULTS_BUCKET = os.getenv("GCS_RESULTS_BUCKET") or os.getenv("GCS_DEST_BUCKET")
GCS_RESULTS_PREFIX = os.getenv("GCS_CIRCULARITY_PREFIX", "results/circularity/")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")


def _gcs_client() -> Optional[storage.Client]:
    try:
        return storage.Client(project=GCP_PROJECT_ID)
    except Exception:
        return None


def _hash_payload(payload: Dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


# Baseline energy for credits (must match LCA baseline logic)
BASELINE_ENERGY_MJ_PER_KG = {
    "aluminium": {"primary": 200.0, "recycled": 20.0},
    "aluminum":  {"primary": 200.0, "recycled": 20.0},
    "copper":    {"primary": 80.0,  "recycled": 20.0},
    "steel":     {"primary": 30.0,  "recycled": 10.0},
}

# Energy price (USD/MJ) for simple cost savings proxy. ~0.09 USD/kWh ≈ 0.025 USD/MJ
ENERGY_PRICE_USD_PER_MJ = float(os.getenv("ENERGY_PRICE_USD_PER_MJ", "0.025"))

# Substitution factor at EoL (how much recycled material displaces primary)
SUBSTITUTION_FACTOR = float(os.getenv("SUBSTITUTION_FACTOR", "0.9"))


def _get_mass_kg(payload: Dict[str, Any]) -> float:
    fu = payload.get("functional_unit") or {}
    unit = (fu.get("unit") or "kg").strip().lower()
    val = float(fu.get("value") or 1.0)
    if unit in ("kg", "kilogram", "kilograms"):
        return val
    if unit in ("g", "gram", "grams"):
        return val / 1000.0
    if unit in ("t", "tonne", "tonnes", "metric_ton", "metric_tonne"):
        return val * 1000.0
    pm = payload.get("product_mass_kg")
    return float(pm) if pm is not None else 1.0


def _get_energy_mix_ef_kg_per_kwh(energy_mix: Dict[str, Any]) -> float:
    if not energy_mix:
        return 0.45
    if "grid_region" in energy_mix:
        return 0.45
    grid = {
        "renewable": 0.05,
        "coal": 0.90,
        "gas": 0.45,
        "oil": 0.75,
        "nuclear": 0.012,
        "other": 0.40,
    }
    total = 0.0
    ef = 0.0
    for k, p in energy_mix.items():
        if k in grid:
            total += float(p or 0.0)
            ef += grid[k] * float(p or 0.0)
    return (ef / total) if total > 0 else 0.45


def analyze_circularity(completed_payload: Dict[str, Any],
                        lca_results: Dict[str, Any],
                        store_to_gcs: bool = True) -> Tuple[Dict[str, Any], list]:
    """
    Rule-based circularity analysis and recommendations.
    Returns (circularity_json, issues)
    """
    issues = []
    metal = (completed_payload.get("metal") or "").strip().lower() or "aluminium"
    route = (completed_payload.get("process_route") or "primary").strip().lower()
    eol = completed_payload.get("end_of_life") or {}
    rr_pct = float(eol.get("recycling_rate_pct") or 0.0)
    reuse_pct = float(eol.get("reuse_pct") or 0.0)
    landfill_pct = float(eol.get("landfill_pct") or max(0.0, 100.0 - rr_pct - reuse_pct))
    mass_kg = _get_mass_kg(completed_payload)
    ef_grid = _get_energy_mix_ef_kg_per_kwh(completed_payload.get("energy_mix") or {})

    metal_tbl = BASELINE_ENERGY_MJ_PER_KG.get(metal) or BASELINE_ENERGY_MJ_PER_KG["aluminium"]
    e_primary = float(metal_tbl["primary"])
    e_recycled = float(metal_tbl["recycled"])
    delta_energy_per_kg = max(0.0, e_primary - e_recycled)

    credited_kg = mass_kg * (rr_pct / 100.0) * SUBSTITUTION_FACTOR
    energy_savings_MJ = delta_energy_per_kg * credited_kg
    cost_savings_usd = energy_savings_MJ * ENERGY_PRICE_USD_PER_MJ

    emission_savings_kg = (energy_savings_MJ / 3.6) * ef_grid

    recs = []
    if rr_pct < 80.0:
        recs.append("Increase recycling to at least 80% to unlock more energy and emission savings.")
    if reuse_pct < 10.0:
        recs.append("Explore design-for-reuse to raise reuse above 10% and extend product life.")
    if landfill_pct > 20.0:
        recs.append("Reduce landfill below 20% via better collection and sorting.")
    if route == "primary" and rr_pct >= 50.0:
        recs.append("Shift more feedstock to recycled route where feasible to lower process energy.")

    recommendation = " ".join(recs) if recs else "Your circularity metrics look strong; maintain and monitor performance."

    results = {
        "metal": metal,
        "process_route": route,
        "functional_unit": completed_payload.get("functional_unit"),
        "recycling_rate_pct": rr_pct,
        "reuse_pct": reuse_pct,
        "landfill_pct": landfill_pct,
        "mass_assessed_kg": mass_kg,
        "savings": {
            "energy_MJ": round(energy_savings_MJ, 3),
            "emissions_kgCO2": round(emission_savings_kg, 3),
            "cost_savings_usd": round(cost_savings_usd, 2),
        },
        "recommendation": recommendation,
        "source_payload_hash": lca_results.get("source_payload_hash") or _hash_payload(completed_payload),
        "references": {
            "substitution_factor": SUBSTITUTION_FACTOR,
            "energy_price_usd_per_mj": ENERGY_PRICE_USD_PER_MJ,
            "note": "Heuristic MVP based on energy deltas between primary and recycled routes.",
        },
    }

    if store_to_gcs and GCS_RESULTS_BUCKET:
        try:
            client = _gcs_client()
            if client:
                bucket = client.bucket(GCS_RESULTS_BUCKET)
                obj = f"{GCS_RESULTS_PREFIX}{results['source_payload_hash']}.json"
                bucket.blob(obj).upload_from_string(json.dumps(results, ensure_ascii=False, indent=2), content_type="application/json")
                results["gcs_uri"] = f"gs://{GCS_RESULTS_BUCKET}/{obj}"
        except Exception as e:
            results.setdefault("issues", []).append(f"GCS store failed: {e}")

    return results, issues
