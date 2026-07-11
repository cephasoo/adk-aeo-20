"""
site_mapper.py — Lightweight, portable site structure and product line mapping tools.
Only downloads the homepage and robots.txt (no deep crawling) to keep things fast and server-safe.
"""

import os
import re
import json
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

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
            print(f"[!] Warning: Failed to initialize Gemini model in site_mapper: {e}")
    return _model

def discover_site_structure(url: str) -> str:
    """
    Parses homepage navigation menus and sitemap indexes to map the top-level
    subdomains and subdirectories of a site ("seeing the forest for the tree").
    """
    if not url.startswith("http"):
        url = "https://" + url

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # 1. Fetch Homepage Navigation links
    nav_links = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract links inside nav, header, or menu elements
            navs = soup.find_all(['nav', 'header', 'aside'])
            # Fallback to search list of classes containing menu or nav
            if not navs:
                navs = soup.find_all(class_=re.compile(r'nav|menu|header', re.IGNORECASE))
            
            seen_hrefs = set()
            for container in (navs if navs else [soup]):
                for a in container.find_all('a', href=True):
                    href = a['href'].strip()
                    text = a.get_text().strip().replace("\n", " ")
                    # Resolve relative URLs
                    full_href = urljoin(url, href)
                    if full_href not in seen_hrefs and text:
                        seen_hrefs.add(full_href)
                        nav_links.append({"text": text, "url": full_href})
    except Exception as e:
        print(f"[!] Error fetching homepage in discover_site_structure: {e}")

    # 2. Fetch Robots.txt & Sitemap Index Names (no deep pages)
    sitemaps = []
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        robots_resp = requests.get(robots_url, headers=headers, timeout=5)
        if robots_resp.status_code == 200:
            for line in robots_resp.text.split("\n"):
                if line.lower().startswith("sitemap:"):
                    sitemaps.append(line.split(":", 1)[1].strip())
    except Exception as e:
        print(f"[!] Error fetching robots.txt: {e}")

    # If sitemaps found, fetch only the root sitemaps to see names (no page URLs)
    sitemap_names = []
    for sm in sitemaps[:3]: # Limit to first 3 sitemap links to avoid large responses
        try:
            sm_resp = requests.get(sm, headers=headers, timeout=5)
            if sm_resp.status_code == 200:
                # Find sitemap locations/names
                sm_soup = BeautifulSoup(sm_resp.text, 'xml')
                locs = sm_soup.find_all('loc')
                for l in locs[:10]: # Limit to top 10 loc names
                    sitemap_names.append(l.get_text().strip())
        except Exception:
            pass

    # 3. Call Gemini to Synthesize the Top-Level Map
    model = get_model()
    if not model:
        return "Error: Gemini model client is not configured/available."

    prompt = f"""
Analyze the following homepage navigation menu links and sitemap URLs for: "{url}".
Infer the overall website architecture, listing:
1. Active subdomains (e.g. blog.brand.com, app.brand.com).
2. Major top-level directories and categories (e.g. /products/, /pricing/, /resources/).

Homepage Menu Links:
{json.dumps(nav_links[:40], indent=2)}

Sitemaps / Locations:
{json.dumps(sitemap_names[:20], indent=2)}

Respond ONLY with a clean, text-based hierarchical directory tree (indented with spaces) that shows "the forest for the tree" (do NOT list individual posts or deep content pages).
"""
    try:
        response = model.api_client.models.generate_content(
            model=model.model,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: Failed to synthesize site structure using Gemini: {e}"

def map_product_lines(url: str) -> str:
    """
    Parses homepage navigation menu text and URLs, and uses Gemini to map out
    the brand's core product lines, modules, or services.
    """
    if not url.startswith("http"):
        url = "https://" + url

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    # 1. Fetch Homepage Navigation menu
    nav_links = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            navs = soup.find_all(['nav', 'header'])
            if not navs:
                navs = soup.find_all(class_=re.compile(r'nav|menu|header', re.IGNORECASE))
            
            seen_hrefs = set()
            for container in (navs if navs else [soup]):
                for a in container.find_all('a', href=True):
                    href = a['href'].strip()
                    text = a.get_text().strip().replace("\n", " ")
                    full_href = urljoin(url, href)
                    if full_href not in seen_hrefs and text:
                        seen_hrefs.add(full_href)
                        nav_links.append({"text": text, "url": full_href})
    except Exception as e:
        return f"Error: Failed to fetch target URL: {e}"

    # 2. Call Gemini to Classify Product Lines
    model = get_model()
    if not model:
        return "Error: Gemini model client is not configured/available."

    prompt = f"""
Analyze the navigation links and menu anchors for: "{url}".
Identify the brand's primary product lines, software modules, or service offerings.

Navigation Links:
{json.dumps(nav_links[:50], indent=2)}

Create a structured markdown table summarizing:
- **Product Line / Service Name**
- **Type** (e.g. Core Platform, Add-on Module, Integration, Service)
- **Target Audience / Purpose**
- **URL**
"""
    try:
        response = model.api_client.models.generate_content(
            model=model.model,
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: Failed to map product lines using Gemini: {e}"
