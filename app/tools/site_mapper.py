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

    # 2. Fetch Robots.txt Sitemap Links
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

    # 3. Dynamic Sitemap Traverser (with cross-subdomain/sitemapindex discovery)
    sitemaps_to_crawl = list(sitemaps)
    # If no sitemaps found in robots.txt, try standard fallback sitemap.xml
    if not sitemaps_to_crawl:
        parsed = urlparse(url)
        sitemaps_to_crawl.append(f"{parsed.scheme}://{parsed.netloc}/sitemap.xml")

    visited_sitemaps = set()
    discovered_subdomains = set()
    subdir_map = {}
    
    # Track main domain to distinguish subdomains
    parsed_main = urlparse(url)
    main_domain = parsed_main.netloc.split('@')[-1].split(':')[0]
    discovered_subdomains.add(main_domain)

    # Crawl sitemaps up to max depth of 2 (to prevent infinite loops / token bloat)
    # We will fetch up to 10 sitemap files in total to protect unit economics/speed.
    sitemap_count = 0
    while sitemaps_to_crawl and sitemap_count < 10:
        sm_url = sitemaps_to_crawl.pop(0)
        if sm_url in visited_sitemaps:
            continue
        visited_sitemaps.add(sm_url)
        sitemap_count += 1

        try:
            sm_resp = requests.get(sm_url, headers=headers, timeout=5)
            if sm_resp.status_code == 200:
                try:
                    sm_soup = BeautifulSoup(sm_resp.text, 'xml')
                except Exception:
                    sm_soup = BeautifulSoup(sm_resp.text, 'html.parser')
                
                # Check if it is a Sitemap Index
                sitemap_tags = sm_soup.find_all('sitemap')
                if sitemap_tags:
                    for tag in sitemap_tags:
                        loc_tag = tag.find('loc')
                        if loc_tag:
                            nested_url = loc_tag.get_text().strip()
                            sitemaps_to_crawl.append(nested_url)
                            # Discover subdomain from the sitemap URL
                            nest_parsed = urlparse(nested_url)
                            nest_domain = nest_parsed.netloc.split('@')[-1].split(':')[0]
                            if nest_domain.endswith(main_domain) and nest_domain != main_domain:
                                discovered_subdomains.add(nest_domain)
                
                # Check for URLs (URL Set)
                url_tags = sm_soup.find_all('url')
                for tag in url_tags:
                    loc_tag = tag.find('loc')
                    if loc_tag:
                        page_url = loc_tag.get_text().strip()
                        # Discover subdomain from the page URL
                        p_parsed = urlparse(page_url)
                        p_domain = p_parsed.netloc.split('@')[-1].split(':')[0]
                        if p_domain.endswith(main_domain) and p_domain != main_domain:
                            discovered_subdomains.add(p_domain)
                        
                        # Process path components for subdirectory grouping
                        path_parts = [p for p in p_parsed.path.split("/") if p]
                        if len(path_parts) > 1:
                            # Subdirectory path (everything except the last part/leaf)
                            subdir_parts = path_parts[:-1]
                            depth = len(subdir_parts)
                            subdir_path = f"/{'/'.join(subdir_parts)}/"
                            
                            # Prefix with subdomain if it is different
                            if p_domain != main_domain:
                                subdir_path = f"[{p_domain}] {subdir_path}"
                            
                            if subdir_path not in subdir_map:
                                subdir_map[subdir_path] = {"depth": depth, "urls": []}
                            if len(subdir_map[subdir_path]["urls"]) < 5:
                                subdir_map[subdir_path]["urls"].append(page_url)
        except Exception as e:
            print(f"[!] Error fetching sitemap {sm_url}: {e}")

    # 4. Call Gemini to Synthesize the Top-Level Map
    model = get_model()
    if not model:
        return "Error: Gemini model client is not configured/available."

    # Pack subdir mapping for the prompt
    subdir_data = {}
    for path, info in subdir_map.items():
        subdir_data[path] = {
            "crawl_depth": info["depth"],
            "examples": info["urls"]
        }

    prompt = f"""
Analyze the following homepage navigation menu links, sitemap index files, subdirectories, and discovered subdomains for: "{url}".
Infer the overall website architecture.

Homepage Menu Links:
{json.dumps(nav_links[:40], indent=2)}

Discovered Subdomains:
{json.dumps(list(discovered_subdomains), indent=2)}

Grouped Subdirectories & Examples (Level 1 to N, Crawl Depth):
{json.dumps(subdir_data, indent=2)}

Google Search Guidelines on Crawl Depth & Orphaned Content:
- Crawling is the first stage of finding pages. Googlebot uses algorithmic processes to choose which pages to crawl.
- Deeply nested directories (Crawl Depth >= 4, requiring more than 3 directory layers or clicks from the homepage) are at high risk of under-crawling, delayed indexation, or becoming "orphaned content" if they lack strong internal link structures.
- A sitemap index or nested sitemaps can map out directories on multiple subdomains.

TASKS:
1. Generate a clean, text-based hierarchical directory tree (indented with spaces) that shows "the forest and the trees" (grouping folders under their respective subdomains, e.g., blog.example.com, and detailing subdirectory paths).
2. Include a **"CRAWL DEPTH & ORPHANED CONTENT RISK AUDIT"** section. Identify any subdirectories with a Crawl Depth of 4 or more, flag them, explain the risk of indexation failures, and provide actionable recommendations.
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
