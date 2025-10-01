# AI-Driven LCA Tool – Data Ingestion Agent (Scaffold)

This repo is being set up to use LangChain with Google Gemini for the Data Ingestion Agent.

## What’s included
- `.env` keys for GCS and Gemini (API key, model)
- `requirements.txt` with LangChain, langchain-google-genai, and GCS libs
- `src/ingestion/langchain_setup.py` helper to construct a Gemini LLM via LangChain
- `.gitignore`

## Next steps
1. Create a Python venv and install requirements.
2. Set environment variables in `.env` (GEMINI_API_KEY, GCS buckets, creds).
3. Implement the ingestion workflow to:
   - Stream-list CSV/PDF files from the source GCS bucket
   - For CSV: parse and map to a normalized JSON schema
   - For PDF: use Gemini via LangChain to extract structured JSON
   - Write results into destination GCS bucket
   - Track processed files (manifest) to avoid reprocessing

## Quickstart (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a service account JSON and point `GOOGLE_APPLICATION_CREDENTIALS` in `.env` to it.
