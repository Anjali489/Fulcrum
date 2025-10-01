from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from google.cloud import storage

from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


# ---------------- Config ----------------
GCS_DEST_BUCKET = os.getenv("GCS_DEST_BUCKET")
GCS_DEST_PREFIX = os.getenv("GCS_DEST_PREFIX", "kb/")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-pro")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY


REQUIRED_SCHEMA = [
    "metal",
    "process_route",             # primary | recycled | mixed
    "functional_unit",           # {unit: str, value: float}
    "system_boundary",           # e.g., Cradle-to-Grave
    "energy_mix",                # {renewable, coal, gas, oil, nuclear, other} or {grid_region}
    "transport",                 # {mode, distance_km, fuel_type}
    "product",                   # {lifetime_years, energy_consumption_kwh_year}
    "end_of_life",               # {recycling_rate_pct, reuse_pct, landfill_pct}
]

STATIC_DEFAULTS = {
    "process_route": "primary",
    "functional_unit": {"unit": "kg", "value": 1.0},
    "system_boundary": "Cradle-to-Grave",
    "energy_mix": {"renewable": 30.0, "coal": 40.0, "gas": 20.0, "oil": 5.0, "nuclear": 5.0, "other": 0.0},
    "transport": {"mode": "truck", "distance_km": 100.0, "fuel_type": "diesel"},
    "product": {"lifetime_years": 10.0, "energy_consumption_kwh_year": 500.0},
    "end_of_life": {"recycling_rate_pct": 50.0, "reuse_pct": 0.0, "landfill_pct": 50.0},
}


def _gcs_client() -> Optional[storage.Client]:
    try:
        return storage.Client(project=GCP_PROJECT_ID)
    except Exception:
        return None


def load_kb_defaults() -> Dict[str, Dict[str, Any]]:
    """Aggregate lightweight defaults by metal from KB JSONs in GCS.
    Looks for either top-level 'structured' with 'metal' or CSV 'records' with 'metal'.
    """
    agg: Dict[str, Dict[str, Any]] = {}
    if not GCS_DEST_BUCKET:
        return agg
    client = _gcs_client()
    if not client:
        return agg

    try:
        bucket = client.bucket(GCS_DEST_BUCKET)
        for blob in bucket.list_blobs(prefix=GCS_DEST_PREFIX):
            if not blob.name.lower().endswith(".json"):
                continue
            try:
                data = json.loads(blob.download_as_text())
            except Exception:
                continue
            # Candidate metal sources
            metal = None
            if isinstance(data, dict):
                if isinstance(data.get("structured"), dict):
                    metal = (data["structured"].get("metal") or "").strip().lower()
                elif isinstance(data.get("records"), list) and data["records"]:
                    first = data["records"][0]
                    metal = (first.get("metal") or "").strip().lower()
                else:
                    metal = (data.get("metal") or "").strip().lower()

            if not metal:
                continue

            m = agg.setdefault(metal, {})
            # Prefer any structured hints
            for key in ("process_route", "energy_mix", "transport", "product", "end_of_life"):
                val = None
                if isinstance(data.get("structured"), dict):
                    val = data["structured"].get(key)
                if val is None and key in data:
                    val = data.get(key)
                if val is None and isinstance(data.get("records"), list) and data["records"]:
                    # try majority or first non-null
                    for r in data["records"]:
                        if key in r:
                            val = r[key]
                            break
                if isinstance(val, dict) and key not in m:
                    m[key] = val
    except Exception:
        # KB load is best-effort
        pass
    return agg


def _build_llm() -> Optional[ChatGoogleGenerativeAI]:
    if not GEMINI_API_KEY:
        return None
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0, google_api_key=GEMINI_API_KEY)


def _llm_fill_missing(base_payload: Dict[str, Any]) -> Dict[str, Any]:
    llm = _build_llm()
    if not llm:
        return {}
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a sustainability engineer. Given partial user input for a metals LCA and circularity analysis, "
            "fill only missing fields using domain norms. Return strictly JSON; no commentary. Use null when unknown."
        )),
        ("human", (
            "Required schema fields: metal, process_route, functional_unit {{unit,value}}, system_boundary, "
            "energy_mix, transport, product, end_of_life.\n"
            "Input JSON:\n{input}\n\nReturn JSON with only these fields at top level."
        ))
    ])
    try:
        resp = (prompt | llm).invoke({"input": json.dumps(base_payload, ensure_ascii=False)})
        content = getattr(resp, "content", None) or (resp if isinstance(resp, str) else "")
        data = json.loads(content)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _norm_end_of_life(eol: Dict[str, Any]) -> Dict[str, float]:
    rr = float(eol.get("recycling_rate_pct") or 0)
    reuse = float(eol.get("reuse_pct") or 0)
    landfill = eol.get("landfill_pct")
    if landfill is None:
        landfill = max(0.0, 100.0 - rr - reuse)
    total = rr + reuse + float(landfill)
    if total > 0:
        # renormalize to 100
        rr = rr * 100.0 / total
        reuse = reuse * 100.0 / total
        landfill = float(landfill) * 100.0 / total
    return {"recycling_rate_pct": rr, "reuse_pct": reuse, "landfill_pct": landfill}


def _norm_energy_mix(mix: Dict[str, Any]) -> Dict[str, float]:
    if "grid_region" in mix:
        return mix  # leave as-is for downstream resolver
    keys = ["renewable", "coal", "gas", "oil", "nuclear", "other"]
    vals = [float(mix.get(k) or 0) for k in keys]
    total = sum(vals)
    if total <= 0:
        return STATIC_DEFAULTS["energy_mix"]
    return {k: v * 100.0 / total for k, v in zip(keys, vals)}


def _merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def parse_and_complete(user_input: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str], Dict[str, str]]:
    """
    Returns: (completed_payload, issues, provenance)
    - completed_payload: JSON ready for LCA + Circularity agents
    - issues: list of unresolved or assumptions made
    - provenance: map of field -> source (user|kb|llm|default)
    """
    issues: List[str] = []
    provenance: Dict[str, str] = {}

    result: Dict[str, Any] = {}
    kb = load_kb_defaults()

    # 1) Start with user input
    result = _merge(result, user_input)
    for k in user_input.keys():
        provenance[k] = "user"

    # 2) If metal present and KB has defaults, merge
    metal_key = (result.get("metal") or "").strip().lower()
    if metal_key and metal_key in kb:
        result = _merge(kb[metal_key], result)  # user overrides KB
        for k in kb[metal_key].keys():
            provenance.setdefault(k, "kb")

    # 3) Add static defaults for anything missing (do not overwrite)
    for k, v in STATIC_DEFAULTS.items():
        if k not in result or result[k] in (None, "", {}):
            result[k] = v
            provenance.setdefault(k, "default")

    # 4) LLM fill for any missing top-level required keys
    missing_top = [k for k in REQUIRED_SCHEMA if k not in result or result[k] in (None, "", {})]
    if missing_top:
        llm_out = _llm_fill_missing(result)
        if isinstance(llm_out, dict):
            for k in REQUIRED_SCHEMA:
                if k in llm_out and llm_out[k] not in (None, "", {}):
                    if k not in result or result[k] in (None, "", {}):
                        result[k] = llm_out[k]
                        provenance[k] = "llm"

    # 5) Normalize nested structures
    if isinstance(result.get("end_of_life"), dict):
        result["end_of_life"] = _norm_end_of_life(result["end_of_life"])
    if isinstance(result.get("energy_mix"), dict):
        result["energy_mix"] = _norm_energy_mix(result["energy_mix"])

    # 6) Validate criticals
    criticals = ["metal", "process_route", "functional_unit", "system_boundary"]
    for c in criticals:
        if c not in result or result[c] in (None, "", {}):
            issues.append(f"Missing critical field: {c}")

    # friendly alias calculations
    # If user provided simple numbers/text, map them into nested structures (already done by app ideally)

    return result, issues, provenance
