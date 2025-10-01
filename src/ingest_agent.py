"""
Single-file Data Ingestion Agent

Features
- Streams from a GCS source bucket (no local download needed)
- Processes CSV and PDF files
- CSV: parse via pandas, map to normalized records
- PDF: extract text (pdfminer); fallback OCR (requires poppler + tesseract) and then parse with Gemini via LangChain
- Structured JSON outputs written to a destination GCS bucket
- Idempotent: skips files that already have an output JSON in dest bucket

Env vars (see .env):
- GCS_SOURCE_BUCKET
- GCS_SOURCE_PREFIX (optional)
- GCS_DEST_BUCKET
- GCS_DEST_PREFIX (optional, default: "kb/")
- GOOGLE_APPLICATION_CREDENTIALS (path to service account JSON)
- GEMINI_API_KEY
- GEMINI_MODEL (default: models/gemini-1.5-pro-latest)

Run (PowerShell):
    python src/ingest_agent.py
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from urllib.parse import urlparse

# GCS
from google.cloud import storage

# CSV
import pandas as pd

# PDF text extraction
from pdfminer.high_level import extract_text as pdf_extract_text

# Optional OCR pipeline (Windows note: requires poppler + tesseract installed separately)
try:
    from pdf2image import convert_from_bytes  # requires poppler installed and in PATH or POPPLER_PATH env var
    import pytesseract  # requires tesseract installed
    from PIL import Image
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

# LangChain + Gemini
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()


# -------------------- Config --------------------
GCS_SOURCE_BUCKET = os.getenv("GCS_SOURCE_BUCKET")
GCS_SOURCE_PREFIX = os.getenv("GCS_SOURCE_PREFIX", "")
GCS_DEST_BUCKET = os.getenv("GCS_DEST_BUCKET")
GCS_DEST_PREFIX = os.getenv("GCS_DEST_PREFIX", "kb/")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-1.5-pro-latest")


def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


def _normalize_bucket_name(value: str) -> str:
    """Accepts a bucket identifier in various forms and returns the plain bucket name.

    Supported inputs:
    - "my-bucket"
    - "gs://my-bucket" or "gs://my-bucket/path" (path ignored)
    - "https://www.googleapis.com/storage/v1/b/<bucket>[/...]"
    - "https://<bucket>.storage.googleapis.com[/...]"
    """
    v = (value or "").strip()
    if not v:
        return v
    # gs://bucket[/...]
    if v.startswith("gs://"):
        return v[5:].split("/", 1)[0]
    # http(s) URLs
    if v.startswith("http://") or v.startswith("https://"):
        try:
            p = urlparse(v)
            # Try API style: /storage/v1/b/<bucket>/...
            parts = [seg for seg in p.path.split("/") if seg]
            if "b" in parts:
                i = parts.index("b")
                if i + 1 < len(parts):
                    return parts[i + 1]
            # Try virtual host style: <bucket>.storage.googleapis.com
            host = p.netloc
            if host.endswith(".storage.googleapis.com"):
                return host[: -len(".storage.googleapis.com")]
        except Exception:
            pass
    # Fallback: assume already a bucket name
    return v


# -------------------- GCS utils --------------------
def get_gcs_client() -> storage.Client:
    # Relies on GOOGLE_APPLICATION_CREDENTIALS or default credentials
    return storage.Client()


def list_source_blobs(client: storage.Client, bucket_name: str, prefix: str = ""):
    bucket = client.bucket(bucket_name)
    return client.list_blobs(bucket, prefix=prefix)


def dest_key_for_source(source_key: str) -> str:
    return f"{GCS_DEST_PREFIX}{source_key}.json"


def is_already_processed(client: storage.Client, dest_bucket_name: str, dest_key: str) -> bool:
    bucket = client.bucket(dest_bucket_name)
    blob = bucket.blob(dest_key)
    return blob.exists()


def write_json_to_gcs(client: storage.Client, bucket_name: str, key: str, data: Dict[str, Any]):
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(key)
    blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=2), content_type="application/json")


def read_blob_text(client: storage.Client, bucket_name: str, key: str, encoding: str = "utf-8") -> str:
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(key)
    return blob.download_as_text(encoding=encoding)


def read_blob_bytes(client: storage.Client, bucket_name: str, key: str) -> bytes:
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(key)
    return blob.download_as_bytes()


# -------------------- CSV processing --------------------
def parse_csv_to_records(csv_text: str) -> List[Dict[str, Any]]:
    """Map CSV rows to normalized records. Heuristic column mapping.
    Recognized columns (case-insensitive substrings):
    - metal
    - process_route|route|process
    - emissions|co2|ghg
    - energy|energy_consumption|mj
    - water|water_use|liters|l
    - transport_mode|mode
    - distance|distance_km|km
    - recycling_rate|recycled|
    """
    df = pd.read_csv(io.StringIO(csv_text))
    cols = {c.lower(): c for c in df.columns}

    def pick(*names):
        for n in names:
            # exact
            if n.lower() in cols:
                return cols[n.lower()]
        # substring heuristic
        for want in names:
            for lc, orig in cols.items():
                if want in lc:
                    return orig
        return None

    c_metal = pick("metal")
    c_route = pick("process_route", "route", "process")
    c_emis = pick("emissions", "co2", "ghg")
    c_energy = pick("energy_consumption", "energy", "mj")
    c_water = pick("water", "water_use", "liters", "l")
    c_mode = pick("transport_mode", "mode")
    c_dist = pick("distance_km", "distance", "km")
    c_rec = pick("recycling_rate", "recycled")

    records: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        rec: Dict[str, Any] = {}
        if c_metal: rec["metal"] = row.get(c_metal)
        if c_route: rec["process_route"] = row.get(c_route)
        if c_emis is not None:
            try:
                rec["emissions_kgCO2"] = float(row.get(c_emis))
            except Exception:
                pass
        if c_energy is not None:
            try:
                rec["energy_MJ"] = float(row.get(c_energy))
            except Exception:
                pass
        if c_water is not None:
            try:
                rec["water_L"] = float(row.get(c_water))
            except Exception:
                pass
        transport: Dict[str, Any] = {}
        if c_mode:
            transport["mode"] = row.get(c_mode)
        if c_dist is not None:
            try:
                transport["distance_km"] = float(row.get(c_dist))
            except Exception:
                pass
        if transport:
            rec["transport"] = transport
        if c_rec is not None:
            try:
                rec.setdefault("end_of_life", {})["recycling_rate"] = float(row.get(c_rec))
            except Exception:
                pass
        # Only include if we captured anything meaningful
        if rec:
            records.append(rec)
    return records


# -------------------- PDF processing --------------------
def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Try reading embedded text; if too little and OCR available, OCR pages."""
    text = ""
    try:
        text = pdf_extract_text(io.BytesIO(pdf_bytes)) or ""
    except Exception:
        text = ""

    if len(text.strip()) >= 200 or not OCR_AVAILABLE:
        return text

    # Fallback OCR
    try:
        images = convert_from_bytes(pdf_bytes)  # type: ignore[name-defined]
        parts: List[str] = []
        for img in images:
            if not isinstance(img, Image.Image):
                img = Image.fromarray(img)
            parts.append(pytesseract.image_to_string(img))  # type: ignore[name-defined]
        ocr_text = "\n".join(parts)
        # If OCR produced substantially more text, prefer it
        if len(ocr_text.strip()) > len(text.strip()):
            return ocr_text
    except Exception:
        pass
    return text


def build_gemini_llm() -> ChatGoogleGenerativeAI:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set in environment")
    return ChatGoogleGenerativeAI(model=GEMINI_MODEL, temperature=0, google_api_key=GEMINI_API_KEY)


def gemini_extraction(text: str) -> Dict[str, Any]:
    """Use Gemini via LangChain to normalize PDF text into structured JSON."""
    llm = build_gemini_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            "You are an expert at extracting structured LCA and circularity data from technical PDFs in metallurgy and mining. "
            "Return only valid JSON, no prose. Use null for unknowns."
        )),
        ("human", (
            "From the given text, extract an object with these fields where applicable:\n"
            "- metal: string\n"
            "- process_route: string (e.g., primary, recycled)\n"
            "- emissions_kgCO2: number\n"
            "- energy_MJ: number\n"
            "- water_L: number\n"
            "- energy_mix: object (e.g., {renewable: %, coal: %, gas: %})\n"
            "- transport: object (mode, distance_km)\n"
            "- end_of_life: object (recycling_rate, landfill)\n"
            "- notes: string (brief 1-2 lines)\n\n"
            "Text:\n{input}"
        )),
    ])
    try:
        resp = (prompt | llm).invoke({"input": text})
        content = getattr(resp, "content", None) or (resp if isinstance(resp, str) else "")
        return json.loads(content)
    except Exception:
        # As a fallback, return minimal structure
        return {"notes": "LLM parsing failed or returned non-JSON."}


# -------------------- Orchestration --------------------
def process_csv_blob(client: storage.Client, src_bucket: str, blob) -> Dict[str, Any]:
    csv_text = read_blob_text(client, src_bucket, blob.name)
    records = parse_csv_to_records(csv_text)
    out = {
        "source": _source_meta(blob, src_bucket),
        "doc_type": "csv",
        "record_count": len(records),
        "records": records,
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }
    return out


def process_pdf_blob(client: storage.Client, src_bucket: str, blob) -> Dict[str, Any]:
    pdf_bytes = read_blob_bytes(client, src_bucket, blob.name)
    text = extract_text_from_pdf_bytes(pdf_bytes)
    structured = gemini_extraction(text)
    out = {
        "source": _source_meta(blob, src_bucket),
        "doc_type": "pdf",
        "structured": structured,
        "text_excerpt": text[:2000],  # cap to avoid huge JSONs
        "extracted_at": datetime.now(timezone.utc).isoformat(),
    }
    return out


def _source_meta(blob, bucket_name: str) -> Dict[str, Any]:
    # blob.updated may be None in some edge cases
    updated = None
    try:
        if hasattr(blob, "updated") and blob.updated:
            updated = blob.updated.astimezone(timezone.utc).isoformat()
    except Exception:
        updated = None
    return {
        "bucket": bucket_name,
        "key": blob.name,
        "size": getattr(blob, "size", None),
        "crc32c": getattr(blob, "crc32c", None),
        "md5_hash": getattr(blob, "md5_hash", None),
        "updated": updated,
        "content_type": getattr(blob, "content_type", None),
    }


def run_ingestion():
    source_bucket_raw = GCS_SOURCE_BUCKET or _require_env("GCS_SOURCE_BUCKET")
    dest_bucket_raw = GCS_DEST_BUCKET or _require_env("GCS_DEST_BUCKET")

    source_bucket = _normalize_bucket_name(source_bucket_raw)
    dest_bucket = _normalize_bucket_name(dest_bucket_raw)

    # Validate that we ended up with plain bucket names
    for label, b in ("GCS_SOURCE_BUCKET", source_bucket), ("GCS_DEST_BUCKET", dest_bucket):
        if not b or "://" in b or "/" in b:
            raise RuntimeError(f"{label} must be a bucket name like 'my-bucket', not a URL. Got: {b!r}")

    client = get_gcs_client()

    print(f"Listing from gs://{source_bucket}/{GCS_SOURCE_PREFIX} ...")
    blobs = list(list_source_blobs(client, source_bucket, GCS_SOURCE_PREFIX))
    print(f"Found {len(blobs)} candidates")

    processed = 0
    skipped = 0
    failed = 0

    for blob in blobs:
        name_lc = blob.name.lower()
        if not (name_lc.endswith(".csv") or name_lc.endswith(".pdf")):
            continue
        dest_key = dest_key_for_source(blob.name)
        if is_already_processed(client, dest_bucket, dest_key):
            skipped += 1
            continue

        print(f"Processing {blob.name} ...")
        try:
            if name_lc.endswith(".csv"):
                out = process_csv_blob(client, source_bucket, blob)
            else:
                out = process_pdf_blob(client, source_bucket, blob)

            write_json_to_gcs(client, dest_bucket, dest_key, out)
            print(f"Wrote gs://{dest_bucket}/{dest_key}")
            processed += 1
        except Exception as e:
            failed += 1
            print(f"Error processing {blob.name}: {e}")

    print(f"Done. processed={processed} skipped={skipped} failed={failed}")


if __name__ == "__main__":
    try:
        run_ingestion()
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
