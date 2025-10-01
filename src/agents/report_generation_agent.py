from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

GCS_RESULTS_BUCKET = os.getenv("GCS_RESULTS_BUCKET") or os.getenv("GCS_DEST_BUCKET")
GCS_REPORTS_PREFIX = os.getenv("GCS_REPORTS_PREFIX", "results/reports/")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")


def _gcs_client() -> Optional[storage.Client]:
    try:
        return storage.Client(project=GCP_PROJECT_ID)
    except Exception:
        return None


def generate_report(payload: Dict[str, Any],
                    lca_results: Dict[str, Any],
                    circularity_results: Dict[str, Any],
                    store_to_gcs: bool = True) -> Tuple[Dict[str, Any], list]:
    """
    Build a structured report JSON combining inputs and results for rendering and export.
    Returns (report_json, issues)
    """
    issues = []
    meta = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "metal": payload.get("metal"),
        "process_route": payload.get("process_route"),
        "functional_unit": payload.get("functional_unit"),
        "system_boundary": payload.get("system_boundary"),
    }

    totals = (lca_results or {}).get("totals", {})
    breakdown = (lca_results or {}).get("breakdown", {})
    energy_mix = (lca_results or {}).get("energy_mix") or payload.get("energy_mix") or {}
    transport = (lca_results or {}).get("transport") or payload.get("transport") or {}
    circ = circularity_results or {}

    report = {
        "meta": meta,
        "kpis": {
            "emissions_kgCO2": totals.get("emissions_kgCO2"),
            "energy_MJ": totals.get("energy_MJ"),
            "water_L": totals.get("water_L"),
            "waste_kg": totals.get("waste_kg"),
        },
        "breakdown": breakdown,
        "energy_mix": energy_mix,
        "transport": transport,
        "circularity": {
            "recycling_rate_pct": circ.get("recycling_rate_pct"),
            "reuse_pct": circ.get("reuse_pct"),
            "landfill_pct": circ.get("landfill_pct"),
            "savings": circ.get("savings", {}),
            "recommendation": circ.get("recommendation"),
        },
        "sources": {
            "lca_gcs_uri": lca_results.get("gcs_uri") if isinstance(lca_results, dict) else None,
            "circularity_gcs_uri": circularity_results.get("gcs_uri") if isinstance(circularity_results, dict) else None,
        },
    }

    # Optional: store to GCS
    if store_to_gcs and GCS_RESULTS_BUCKET:
        try:
            client = _gcs_client()
            if client:
                bucket = client.bucket(GCS_RESULTS_BUCKET)
                # Try to re-use LCA hash for consistent naming
                name_hash = (lca_results or {}).get("source_payload_hash") or "report"
                obj = f"{GCS_REPORTS_PREFIX}{name_hash}.json"
                bucket.blob(obj).upload_from_string(
                    json.dumps(report, ensure_ascii=False, indent=2),
                    content_type="application/json",
                )
                report.setdefault("sources", {})["report_gcs_uri"] = f"gs://{GCS_RESULTS_BUCKET}/{obj}"
        except Exception as e:
            issues.append(f"GCS store failed: {e}")

    return report, issues
