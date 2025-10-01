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
GCS_RESULTS_PREFIX = os.getenv("GCS_RESULTS_PREFIX", "results/lca/")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

# Simplified baseline factors per metal and route (per kg of product)
BASELINE_FACTORS = {
    "aluminium": {
        "primary":  {"energy_MJ_per_kg": 200.0, "water_L_per_kg": 15.0, "waste_kg_per_kg": 0.20},
        "recycled": {"energy_MJ_per_kg": 20.0,  "water_L_per_kg": 5.0,  "waste_kg_per_kg": 0.05},
    },
    "aluminum": {
        "primary":  {"energy_MJ_per_kg": 200.0, "water_L_per_kg": 15.0, "waste_kg_per_kg": 0.20},
        "recycled": {"energy_MJ_per_kg": 20.0,  "water_L_per_kg": 5.0,  "waste_kg_per_kg": 0.05},
    },
    "copper": {
        "primary":  {"energy_MJ_per_kg": 80.0,  "water_L_per_kg": 10.0, "waste_kg_per_kg": 0.10},
        "recycled": {"energy_MJ_per_kg": 20.0,  "water_L_per_kg": 4.0,  "waste_kg_per_kg": 0.03},
    },
    "steel": {
        "primary":  {"energy_MJ_per_kg": 30.0,  "water_L_per_kg": 5.0,  "waste_kg_per_kg": 0.05},
        "recycled": {"energy_MJ_per_kg": 10.0,  "water_L_per_kg": 2.0,  "waste_kg_per_kg": 0.02},
    },
}

# Electricity grid emission factors (kgCO2e/kWh)
GRID_EF_KG_PER_KWH = {
    "renewable": 0.05,
    "coal": 0.90,
    "gas": 0.45,
    "oil": 0.75,
    "nuclear": 0.012,
    "other": 0.40,
}
GRID_EF_FALLBACK = 0.45  # used if only grid_region provided or invalid mix

# Transport emission factors (kgCO2e per tonne-km)
TRANSPORT_EF_KG_PER_TKM = {
    "truck": 0.12,
    "road": 0.12,
    "rail": 0.03,
    "sea": 0.01,
    "ship": 0.01,
    "air": 0.60,
}


def _gcs_client() -> Optional[storage.Client]:
    try:
        return storage.Client(project=GCP_PROJECT_ID)
    except Exception:
        return None


def _hash_payload(payload: Dict[str, Any]) -> str:
    s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


def _get_mass_kg(payload: Dict[str, Any]) -> Tuple[float, Optional[str]]:
    fu = payload.get("functional_unit") or {}
    unit = (fu.get("unit") or "kg").strip().lower()
    val = float(fu.get("value") or 1.0)
    issue = None
    if unit in ("kg", "kilogram", "kilograms"):
        return val, None
    if unit in ("g", "gram", "grams"):
        return val / 1000.0, None
    if unit in ("t", "tonne", "tonnes", "metric_ton", "metric_tonne"):
        return val * 1000.0, None
    pm = payload.get("product_mass_kg")
    if pm is not None:
        try:
            return float(pm), None
        except Exception:
            pass
    issue = f"Unknown functional unit '{unit}'; assumed {val} {unit} ≈ 1.0 kg."
    return 1.0, issue


def _grid_ef_from_mix(energy_mix: Dict[str, Any]) -> float:
    if "grid_region" in energy_mix:
        return GRID_EF_FALLBACK
    total = 0.0
    ef = 0.0
    for k, pct in energy_mix.items():
        if k not in GRID_EF_KG_PER_KWH:
            continue
        p = float(pct or 0.0)
        total += p
        ef += GRID_EF_KG_PER_KWH[k] * p
    if total <= 0:
        return GRID_EF_FALLBACK
    return ef / total


def _transport_emissions_kg(transport: Dict[str, Any], mass_kg: float) -> float:
    mode = (transport.get("mode") or "truck").strip().lower()
    distance_km = float(transport.get("distance_km") or 0.0)
    ef = TRANSPORT_EF_KG_PER_TKM.get(mode, TRANSPORT_EF_KG_PER_TKM["truck"])
    tonne_km = (mass_kg / 1000.0) * distance_km
    return ef * tonne_km


def _baseline_for(payload: Dict[str, Any]) -> Dict[str, float]:
    metal = (payload.get("metal") or "").strip().lower()
    route = (payload.get("process_route") or "primary").strip().lower()
    metal_tbl = BASELINE_FACTORS.get(metal) or BASELINE_FACTORS.get("aluminium")
    return metal_tbl.get(route) or list(metal_tbl.values())[0]


def compute_lca(completed_payload: Dict[str, Any], store_to_gcs: bool = True) -> Tuple[Dict[str, Any], list]:
    """
    Deterministic LCA: returns (results_json, issues)
    results_json contains a simple stage breakdown and totals.
    """
    issues = []

    # Extract inputs
    mass_kg, unit_issue = _get_mass_kg(completed_payload)
    if unit_issue:
        issues.append(unit_issue)

    baseline = _baseline_for(completed_payload)
    energy_mix = completed_payload.get("energy_mix") or {}
    transport = completed_payload.get("transport") or {}

    # Process energy and emissions
    energy_MJ_per_kg = float(baseline["energy_MJ_per_kg"])
    energy_MJ = energy_MJ_per_kg * mass_kg

    grid_ef = _grid_ef_from_mix(energy_mix)  # kgCO2/kWh
    process_emissions_kg = (energy_MJ / 3.6) * grid_ef  # MJ -> kWh

    # Transport emissions
    transport_emissions_kg = _transport_emissions_kg(transport, mass_kg)

    # Water and waste
    water_L = float(baseline["water_L_per_kg"]) * mass_kg
    waste_kg = float(baseline["waste_kg_per_kg"]) * mass_kg

    totals = {
        "energy_MJ": round(energy_MJ, 3),
        "emissions_kgCO2": round(process_emissions_kg + transport_emissions_kg, 3),
        "water_L": round(water_L, 3),
        "waste_kg": round(waste_kg, 3),
    }
    breakdown = {
        "process": {
            "energy_MJ": round(energy_MJ, 3),
            "emissions_kgCO2": round(process_emissions_kg, 3),
            "water_L": round(water_L, 3),
            "waste_kg": round(waste_kg, 3),
        },
        "transport": {
            "emissions_kgCO2": round(transport_emissions_kg, 3),
            "distance_km": float(transport.get("distance_km") or 0.0),
            "mode": (transport.get("mode") or "truck"),
        },
    }

    results = {
        "metal": completed_payload.get("metal"),
        "process_route": completed_payload.get("process_route"),
        "functional_unit": completed_payload.get("functional_unit"),
        "system_boundary": completed_payload.get("system_boundary"),
        "energy_mix": energy_mix,
        "transport": transport,
        "totals": totals,
        "breakdown": breakdown,
        "source_payload_hash": _hash_payload(completed_payload),
    }

    # Optional store to GCS
    if store_to_gcs and GCS_RESULTS_BUCKET:
        try:
            client = _gcs_client()
            if client:
                bucket = client.bucket(GCS_RESULTS_BUCKET)
                obj = f"{GCS_RESULTS_PREFIX}{results['source_payload_hash']}.json"
                bucket.blob(obj).upload_from_string(json.dumps(results, ensure_ascii=False, indent=2), content_type="application/json")
                results["gcs_uri"] = f"gs://{GCS_RESULTS_BUCKET}/{obj}"
        except Exception as e:
            issues.append(f"GCS store failed: {e}")

    return results, issues
