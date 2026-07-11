"""
geo_utils.py — Geotargeting and location resolution utilities to prevent location bias in SERP searches.
"""

from urllib.parse import urlparse
import re
import json
import os

_model = None

def get_model():
    global _model
    if _model is None:
        try:
            from google.adk.models import Gemini
            from app.config import DEFAULT_GEMINI_MODEL
            api_key = os.environ.get("GEMINI_API_KEY")
            _model = Gemini(model=DEFAULT_GEMINI_MODEL, api_key=api_key)
        except Exception as e:
            print(f"[!] Warning: Failed to initialize Gemini model in geo_utils: {e}")
    return _model

def resolve_target_region(query: str, url: str = "") -> tuple[str, str]:
    """
    Resolves the most appropriate Google search country code (gl) and canonical location 
    name (location) for SerpAPI based on the query text and target URL.
    Uses Gemini to dynamically extract the location, falling back to TLD mapping if offline or failed.
    """
    query_lower = query.lower() if query else ""
    url_lower = url.lower() if url else ""

    # 1. Primary Route: Try dynamic extraction using Gemini
    model = get_model()
    if model:
        try:
            prompt = f"""
Analyze the search query and target URL to determine the most appropriate Google Search country code (gl) and canonical location name for localized search targeting.

Search Query: "{query}"
Target URL: "{url}"

Respond with ONLY a JSON object containing "gl" (two-letter country code in lowercase, e.g., "ng", "uk", "us", "ca", "de", "na") and "location" (canonical country name, e.g., "Nigeria", "United Kingdom", "United States", "Canada", "Germany", "Namibia"). Do not include markdown code block formatting or any other text.
"""
            response = model.api_client.models.generate_content(
                model=model.model,
                contents=prompt
            )
            text = response.text.strip()
            # Strip markdown block formatting if present
            if text.startswith("```"):
                lines = text.split("\n")
                if lines[0].startswith("```json") or lines[0].startswith("```"):
                    lines = lines[1:-1]
                text = "\n".join(lines).strip()

            data = json.loads(text)
            gl = data.get("gl", "").strip().lower()
            location = data.get("location", "").strip()
            if gl and location:
                return gl, location
        except Exception as e:
            print(f"[!] Warning: Geotargeting LLM resolution failed (falling back): {e}")

    # 2. Secondary Route: Fast Local TLD Fallback
    tld = ""
    if url_lower:
        try:
            parsed_url = urlparse(url_lower)
            netloc = parsed_url.netloc or parsed_url.path
            netloc = netloc.split('@')[-1].split(':')[0]
            parts = netloc.split('.')
            if len(parts) >= 2:
                if len(parts) >= 3 and parts[-2] in ["co", "com", "org", "net", "gov", "edu"]:
                    tld = "." + ".".join(parts[-2:])
                else:
                    tld = "." + parts[-1]
        except Exception:
            pass

    # Simple TLD check
    if tld.endswith(".ng"):
        return "ng", "Nigeria"
    elif tld.endswith(".uk") or tld.endswith(".gb"):
        return "uk", "United Kingdom"
    elif tld.endswith(".ca"):
        return "ca", "Canada"
    elif tld.endswith(".au"):
        return "au", "Australia"
    elif tld.endswith(".za"):
        return "za", "South Africa"
    elif tld.endswith(".de"):
        return "de", "Germany"
    elif tld.endswith(".fr"):
        return "fr", "France"
    elif tld.endswith(".sg"):
        return "sg", "Singapore"
    elif tld.endswith(".na"):
        return "na", "Namibia"

    # Keywords in query fallback
    if "nigeria" in query_lower or "nigerian" in query_lower:
        return "ng", "Nigeria"
    elif "united kingdom" in query_lower or "london" in query_lower or " uk " in query_lower:
        return "uk", "United Kingdom"
    elif "canada" in query_lower or "canadian" in query_lower:
        return "ca", "Canada"
    elif "australia" in query_lower or "australian" in query_lower:
        return "au", "Australia"
    elif "namibia" in query_lower or "namibian" in query_lower:
        return "na", "Namibia"

    # 3. Tertiary Route: Default Fallback
    return "us", "United States"
