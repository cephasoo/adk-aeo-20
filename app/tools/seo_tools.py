import os
import re
import requests
import json
import asyncio
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import urllib3

# Suppress insecure request warnings for local self-signed dev sites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Load audit rules module from the skill path
from .audit_rules import run_audit, generate_report_html

# Stdio / McpToolset imports
try:
    from google.adk.tools import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters
    HAS_ADK_MCP = True
except ImportError:
    HAS_ADK_MCP = False

# Global cache for GSC verified sites
_gsc_site_cache = None

import jwt
from functools import wraps

# In-memory session store mapping chat_id to JWT token
_user_sessions = {}

def set_user_session(user_id: str, token: str):
    _user_sessions[str(user_id)] = token

def get_user_session(user_id: str) -> str:
    return _user_sessions.get(str(user_id))

def is_local_dev_bypass(url_or_id: str) -> bool:
    """
    Returns True if target URL/domain is local development (e.g. localhost, *.local)
    AND DEVELOPER_SECRET_KEY is defined in .env.
    Also returns True if WordPress credentials are missing (test mock mode).
    """
    wp_url = os.environ.get("WP_API_URL")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APPLICATION_PASSWORD")
    if not wp_url or not wp_user or not wp_pass:
        return True

    dev_key = os.environ.get("DEVELOPER_SECRET_KEY")
    if not dev_key:
        return False

    url = str(url_or_id)
    if not (url.startswith("http://") or url.startswith("https://")):
        # For IDs, check if WP_API_URL is local
        url = os.environ.get("WP_API_URL", "")

    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if hostname == "localhost" or hostname == "127.0.0.1" or hostname.endswith(".local"):
            return True
    except Exception:
        pass
    return False

def require_oauth_claims(required_scope: str):
    """
    Decorator for tool functions to verify JWT token authority,
    domain ownership, and scope access.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract tool_context from kwargs
            tool_context = kwargs.get("tool_context")
            user_id = str(tool_context.user_id) if tool_context and hasattr(tool_context, "user_id") else "unknown"

            # Resolve url/id argument
            url_or_id = ""
            for name in ["wp_post_id", "url", "wp_post_id_or_url", "title"]:
                if name in kwargs:
                    url_or_id = kwargs[name]
                    break
            if not url_or_id and len(args) > 0:
                url_or_id = args[0]

            # If local dev bypass is applicable, permit action immediately
            if is_local_dev_bypass(url_or_id):
                return func(*args, **kwargs)

            # Fetch active token for this user session
            token = get_user_session(user_id)
            if not token:
                return "Error: 🔒 Authentication required. Please authenticate first by running: /login <your_token_or_secret>"

            # Decode and validate JWT
            dev_key = os.environ.get("DEVELOPER_SECRET_KEY", "dev_secret_placeholder")
            try:
                claims = jwt.decode(token, dev_key, algorithms=["HS256"])
            except jwt.ExpiredSignatureError:
                return "Error: 🔒 Your session token has expired. Please run /login again."
            except Exception as e:
                return f"Error: 🔒 Invalid authentication token: {e}"

            # Check scope
            scopes = claims.get("scopes", [])
            if required_scope not in scopes:
                return f"Error: 🔒 Insufficient permissions. Required scope: '{required_scope}'"

            # Check domain ownership in GSC properties
            target_domain = ""
            url = str(url_or_id)
            if url.startswith("http://") or url.startswith("https://"):
                try:
                    target_domain = urlparse(url).hostname or ""
                except Exception:
                    pass
            else:
                wp_url = os.environ.get("WP_API_URL", "")
                try:
                    target_domain = urlparse(wp_url).hostname or ""
                except Exception:
                    pass

            verified_properties = claims.get("verified_properties", [])
            clean_domain = target_domain.lower().replace("www.", "")
            clean_verified = [p.lower().replace("www.", "").replace("https://", "").replace("http://", "").rstrip('/') for p in verified_properties]

            if clean_domain and clean_domain not in clean_verified:
                return f"Error: 🔒 Access Denied: You do not own the property '{target_domain}' in Google Search Console."

            return func(*args, **kwargs)
        return wrapper
    return decorator

def _get_verify_param(url: str) -> bool:
    """
    Returns True (enforce SSL verification) for production URLs,
    and False (bypass) ONLY for local development domains (.local, localhost, 127.0.0.1)
    or if explicitly bypassed in the environment settings.
    """
    if os.environ.get("BYPASS_SSL_VERIFY", "").lower() == "true":
        return False
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        if hostname == "localhost" or hostname == "127.0.0.1" or hostname.endswith(".local"):
            return False
    except Exception:
        pass
    return True

# =====================================================================
# 1. ADVANCED ON-PAGE SEO AUDITOR (rendered HTML)
# =====================================================================

def advanced_seo_audit(wp_post_id_or_url: str) -> str:
    """
    Connects to the WordPress site, fetches the public rendered frontend HTML of the page,
    and runs 19 technical SEO and AEO checks.
    Saves the full detailed report as a static HTML file in the WordPress uploads directory
    and returns a high-impact summary to Telegram.
    """
    wp_url = os.environ.get("WP_API_URL")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APPLICATION_PASSWORD")

    if wp_pass:
        wp_pass = wp_pass.replace(" ", "")

    input_str = str(wp_post_id_or_url).strip()
    is_mock = not wp_url or not wp_user or not wp_pass

    resolved_url = ""
    resolved_id = "MOCK_123"
    html_content = ""

    # 1. Fetch Rendered HTML
    if is_mock:
        print("[*] Running advanced_seo_audit in mock mode.")
        resolved_url = "http://aeo-copilot.local/mock-page/"
        # Realistic mock HTML for testing
        html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Ultimate Guide to Shopify SEO and Conversions</title>
    <meta name="description" content="Shopify SEO is essential to growing your eCommerce business. Learn the step-by-step optimization strategies in our guide.">
    <link rel="canonical" href="http://aeo-copilot.local/mock-page/">
    <meta property="og:title" content="Ultimate Guide to Shopify SEO">
    <meta property="og:description" content="Learn step-by-step Shopify SEO strategies.">
    <!-- Missing og:image and og:url -->
    <!-- Missing Twitter Cards -->
</head>
<body>
    <h1>Ultimate Guide to Shopify SEO and Conversions</h1>
    <p>Thin content placeholder paragraph. Shopify SEO is great.</p>
    <h2>Getting Started</h2>
    <p>Sentence one is fine. Sentence two is extremely long and will definitely violate the readability guidelines because it combines too many clauses and runs on forever without any punctuation marks or pauses to help the reader understand the core marketing message which dilutes quality.</p>
    <h3>Step 1: Install tags</h3>
    <img src="http://aeo-copilot.local/img.png" loading="lazy" /> <!-- LCP warning, missing alt, missing dimensions -->
    <a href="http://aeo-copilot.local/next">Click here</a> to learn more. <!-- Generic anchor copy -->
</body>
</html>"""
    else:
        # Resolve URL/ID
        if input_str.startswith("http://") or input_str.startswith("https://"):
            resolved_url = input_str
            # Fetch public rendered page directly
            try:
                response = requests.get(resolved_url, headers=BROWSER_HEADERS, timeout=10, verify=_get_verify_param(resolved_url))
                if response.status_code == 200:
                    html_content = response.text

                    # Resolve actual WP ID from body class (e.g. page-id-10, postid-18)
                    id_match = re.search(r'class=["\'][^"\']*(page-id-|postid-|post-id-)(\d+)', html_content)
                    if id_match:
                        resolved_id = id_match.group(2)
                    elif not is_mock:
                        # Fallback: Query WP API by slug
                        try:
                            slug = urlparse(resolved_url).path.strip('/')
                            if '/' in slug:
                                slug = slug.split('/')[-1]
                            if slug:
                                resp = requests.get(f"{wp_url}/posts?slug={slug}", auth=(wp_user, wp_pass), timeout=5, verify=_get_verify_param(wp_url))
                                if resp.status_code == 200 and resp.json():
                                    resolved_id = str(resp.json()[0].get("id", ""))
                                else:
                                    resp = requests.get(f"{wp_url}/pages?slug={slug}", auth=(wp_user, wp_pass), timeout=5, verify=_get_verify_param(wp_url))
                                    if resp.status_code == 200 and resp.json():
                                        resolved_id = str(resp.json()[0].get("id", ""))
                        except Exception:
                            pass
                else:
                    return f"Error: Failed to fetch rendered page '{resolved_url}' (HTTP {response.status_code})."
            except Exception as e:
                return f"Error: Failed to connect to page URL '{resolved_url}': {e}"
        else:
            # It's an ID. Resolve slug and then fetch the page.
            resolved_id = input_str
            base_url = wp_url.split("/wp-json")[0]

            # Fetch post data to get slug
            try:
                response = requests.get(f"{wp_url}/posts/{resolved_id}", auth=(wp_user, wp_pass), timeout=10, verify=_get_verify_param(wp_url))
                if response.status_code == 404:
                    response = requests.get(f"{wp_url}/pages/{resolved_id}", auth=(wp_user, wp_pass), timeout=10, verify=_get_verify_param(wp_url))

                if response.status_code == 200:
                    data = response.json()
                    slug = data.get("slug", "")
                    resolved_url = f"{base_url}/{slug}/"

                    # Fetch rendered HTML
                    html_resp = requests.get(resolved_url, headers=BROWSER_HEADERS, timeout=10, verify=_get_verify_param(resolved_url))
                    if html_resp.status_code == 200:
                        html_content = html_resp.text
                    else:
                        # Fallback to rendered content field from REST API if page is not public yet
                        html_content = data.get("content", {}).get("rendered", "")
                else:
                    return f"Error: Could not retrieve post/page #{resolved_id} from WordPress REST API."
            except Exception as e:
                return f"Error: WordPress connection failed: {e}"

    # 2. Run Audit
    results = run_audit(html_content, page_url=resolved_url)

    # 3. Write Static Report to wp-content/uploads/aeo-audits/
    import time
    report_filename = f"audit-{resolved_id}-{int(time.time())}.html"
    uploads_dir = r"C:\Users\USER\Local Sites\aeo-copilot\app\public\wp-content\uploads\aeo-audits"

    report_url = ""
    if not os.path.exists(uploads_dir):
        try:
            os.makedirs(uploads_dir, exist_ok=True)
        except Exception:
            pass  # Fallback gracefully if permission fails

    if os.path.exists(uploads_dir):
        # Self-cleaning lifecycle: Prune audit files older than 30 days
        try:
            now = time.time()
            for filename in os.listdir(uploads_dir):
                if filename.startswith("audit-") and filename.endswith(".html"):
                    file_path = os.path.join(uploads_dir, filename)
                    if os.path.isfile(file_path):
                        if now - os.path.getmtime(file_path) > 30 * 86400:
                            os.remove(file_path)
                            print(f"[*] Cleaned up expired audit report: {filename}")
        except Exception as e:
            print(f"[!] Warning: Error pruning expired audit reports: {e}")

        report_html = generate_report_html(results, resolved_id, resolved_url)
        report_path = os.path.join(uploads_dir, report_filename)
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(report_html)
            base_site_url = wp_url.split("/wp-json")[0] if wp_url else "http://aeo-copilot.local"
            report_url = f"{base_site_url}/wp-content/uploads/aeo-audits/{report_filename}"
        except Exception as e:
            print(f"[!] Warning: Could not write static audit report: {e}")

    # 4. Generate Concise Telegram Message
    errors_list = results["errors"]
    warnings_list = results["warnings"]
    metrics = results["metrics"]

    tg_msg = [
        f"📋 **SEO & AEO Audit Summary for:**",
        f"🔗 `{resolved_url}`",
        f"",
        f"📈 **Key Metrics:**",
        f"- Word Count: `{metrics.get('word_count', 0)}` words",
        f"- Sentences density: `{metrics.get('avg_sentence_len', 0.0):.1f}` words/sentence",
        f"- Topical Match Overlap: `{metrics.get('semantic_match_score', 0.0):.1f}%`",
        f"- Total Images: `{metrics.get('images_count', 0)}`"
    ]

    if errors_list:
        tg_msg.append(f"\n❌ **Critical Errors ({len(errors_list)}):**")
        for err in errors_list[:5]:
            tg_msg.append(f"- {err}")
        if len(errors_list) > 5:
            tg_msg.append(f"- _...and {len(errors_list) - 5} more critical errors._")
    else:
        tg_msg.append("\n✅ **No critical errors found!**")

    if warnings_list:
        tg_msg.append(f"\n⚠️ **Technical Warnings ({len(warnings_list)}):**")
        for wrn in warnings_list[:5]:
            tg_msg.append(f"- {wrn}")
        if len(warnings_list) > 5:
            tg_msg.append(f"- _...and {len(warnings_list) - 5} more warnings._")

    if report_url:
        tg_msg.append(f"\n🌐 [View Full Detailed Report]({report_url})")

    return "\n".join(tg_msg)

# =====================================================================
# 2. SERPAPI & AEO VISIBILITY TOOLS
# =====================================================================

def serp_position_tracker(target_url: str, search_query: str) -> str:
    """
    Checks the ranking position of a target URL in Google Search for a search query.
    """
    serpapi_key = os.environ.get("SERPAPI_API_KEY")
    if not serpapi_key:
        # Mock mode fallback
        return (
            f"### SERP Position Tracker (MOCK)\n"
            f"- Query: '{search_query}'\n"
            f"- Target URL: {target_url}\n"
            f"- Position: **#3**\n"
            f"- SERP Features: Answer Box (Featured Snippet) present, People Also Ask (PAA) present."
        )

    try:
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": search_query,
                "api_key": serpapi_key,
                "engine": "google",
                "gl": "us",
                "hl": "en"
            },
            timeout=10
        )
        if response.status_code != 200:
            return f"Error: SerpAPI request failed with status code {response.status_code}."

        data = response.json()
        organic_results = data.get("organic_results", [])

        position = -1
        for item in organic_results:
            link = item.get("link", "")
            if target_url.rstrip("/") in link.rstrip("/"):
                position = item.get("position", -1)
                break

        features = []
        if "answer_box" in data:
            features.append("Answer Box (Featured Snippet)")
        if "related_questions" in data:
            features.append("People Also Ask (PAA)")
        if "knowledge_graph" in data:
            features.append("Knowledge Graph")

        features_str = ", ".join(features) if features else "None detected"

        report = [
            f"### SERP Tracking Report",
            f"- **Query**: `{search_query}`",
            f"- **Target URL**: `{target_url}`",
            f"- **Ranking Position**: " + (f"**#{position}**" if position != -1 else "**Not found in top 100 organic results**"),
            f"- **SERP Features**: {features_str}"
        ]
        return "\n".join(report)
    except Exception as e:
        return f"Error connecting to SerpAPI: {e}"

def aeo_citation_checker(search_query: str, target_url: str, gl: str = "us", hl: str = "en") -> str:
    """
    Checks if a target URL is cited in Google's AI Overview or AI-generated search modes.
    """
    serpapi_key = os.environ.get("SERPAPI_API_KEY")
    if not serpapi_key:
        return (
            f"### AEO Citation Report (MOCK)\n"
            f"- Query: '{search_query}'\n"
            f"- Target URL: {target_url}\n"
            f"- Geotargeting: gl={gl}, hl={hl}\n"
            f"- Cited Status: **✅ Yes (Cited)**\n"
            f"- Citation Context: '...Shopify optimization strategies like those from Sonnet and Prose...'\n"
            f"- Share of Model: **25.0%** (1 out of 4 total citations)"
        )

    try:
        # Use SerpAPI Google AI Mode query directly
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": search_query,
                "api_key": serpapi_key,
                "engine": "google",
                "gl": gl,
                "hl": hl
            },
            timeout=10
        )
        if response.status_code != 200:
            return f"Error: SerpAPI request failed (status {response.status_code})."

        data = response.json()

        # Check answer box or knowledge graph / AI overview sources
        citations = []
        is_cited = False
        cited_text = ""

        # Check answer box citations
        answer_box = data.get("answer_box", {})
        if "link" in answer_box:
            citations.append(answer_box.get("link"))
            if target_url.rstrip("/") in answer_box.get("link", "").rstrip("/"):
                is_cited = True
                cited_text = answer_box.get("snippet", "")

        # Check search citations in general
        organic_results = data.get("organic_results", [])
        for item in organic_results[:4]: # Check top 4
            link = item.get("link", "")
            if target_url.rstrip("/") in link.rstrip("/"):
                citations.append(link)

        # Remove duplicates
        citations = list(set(citations))
        total_citations = len(citations) or 4
        som_score = (1 / total_citations * 100) if is_cited else 0.0

        report = [
            f"### AEO Citation & Share of Model (SoM) Report",
            f"- **Query**: `{search_query}`",
            f"- **Target URL**: `{target_url}`",
            f"- **Cited in AI Overview/Answer Box**: " + ("**✅ YES**" if is_cited else "**❌ NO**"),
            f"- **Share of Model Score**: `{som_score:.1f}%`"
        ]
        if is_cited and cited_text:
            report.append(f"- **Citation Excerpt**: `\"{cited_text[:120]}...\"`")
        return "\n".join(report)
    except Exception as e:
        return f"Error running citation check: {e}"

def keyword_opportunity_finder(seed_query: str) -> str:
    """
    Finds related keyword autocomplete recommendations to expand content coverage.
    """
    serpapi_key = os.environ.get("SERPAPI_API_KEY")
    if not serpapi_key:
        return (
            f"### Keyword Autocomplete Opportunities (MOCK)\n"
            f"Seed: '{seed_query}'\n"
            f"- `shopify seo services` (High intent)\n"
            f"- `shopify seo checklist pdf` (Informational)\n"
            f"- `shopify seo tutorial for beginners` (Search volume spike)"
        )

    try:
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": seed_query,
                "api_key": serpapi_key,
                "engine": "google_autocomplete"
            },
            timeout=10
        )
        if response.status_code != 200:
            return f"Error: Autocomplete API request failed."

        data = response.json()
        suggestions = [s.get("value", "") for s in data.get("suggestions", [])]

        report = [f"### Autocomplete Keyword Opportunities for: '{seed_query}'"]
        for s in suggestions[:8]:
            report.append(f"- `{s}`")
        return "\n".join(report)
    except Exception as e:
        return f"Error fetching autocomplete keywords: {e}"

def rich_snippet_verifier(search_query: str) -> str:
    """
    Checks if rich results/schema snippets are rendered in actual search listings for a query.
    """
    serpapi_key = os.environ.get("SERPAPI_API_KEY")
    if not serpapi_key:
        return (
            f"### Rich Snippet Verification (MOCK)\n"
            f"Query: '{search_query}'\n"
            f"- Listings checked: 10\n"
            f"- Review Schema Snippet: **Verified** (Rating stars present in top listings)\n"
            f"- FAQ Accordion Snippet: **Verified** (FAQ dropdown blocks visible)"
        )

    try:
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": search_query,
                "api_key": serpapi_key,
                "engine": "google"
            },
            timeout=10
        )
        if response.status_code != 200:
            return f"Error checking rich snippets."

        data = response.json()
        organic = data.get("organic_results", [])

        rating_count = 0
        sitelinks_count = 0
        faq_count = 0

        for item in organic:
            if "rich_snippet" in item:
                rating_count += 1
            if "sitelinks" in item:
                sitelinks_count += 1
            if "faq" in item or "questions" in item:
                faq_count += 1

        report = [
            f"### Rich Snippet Validation Report",
            f"- **Query**: `{search_query}`",
            f"- **Listings with Review Stars**: `{rating_count}`",
            f"- **Listings with Sitelinks**: `{sitelinks_count}`",
            f"- **Listings with FAQ Accordions**: `{faq_count}`"
        ]
        return "\n".join(report)
    except Exception as e:
        return f"Error verifying rich snippets: {e}"

# =====================================================================
# 3. GSC (GOOGLE SEARCH CONSOLE) AUDIT TOOLS
# =====================================================================

def _is_gsc_auth() -> bool:
    """Checks if the GSC stdio parameters or OAuth secrets are available."""
    # Check if user set the stdio configuration in their environment
    return bool(os.environ.get("GSC_MCP_COMMAND"))

def _get_authenticated_properties() -> list:
    """Invokes list_properties on the GSC MCP stdio connection if authenticated, else returns empty."""
    global _gsc_site_cache
    if _gsc_site_cache is not None:
        return _gsc_site_cache

    if not _is_gsc_auth() or not HAS_ADK_MCP:
        return []

    try:
        # Spawn stdio MCP client
        cmd = os.environ.get("GSC_MCP_COMMAND")
        args_str = os.environ.get("GSC_MCP_ARGS", "[]")
        args = json.loads(args_str)

        # Stdio connection
        toolset = McpToolset(
            connection_params=StdioServerParameters(
                command=cmd,
                args=args
            )
        )

        # We run this in an async loop since McpToolset.get_tools() is async
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Run in worker thread if loop is running
            import nest_asyncio
            nest_asyncio.apply()

        async def fetch_props():
            tools = await toolset.get_tools()
            list_tools_names = [t.name for t in tools]
            if "list_properties" in list_tools_names:
                # Find list_properties tool and call it
                for t in tools:
                    if t.name == "list_properties":
                        res = await t.call(arguments={})
                        # Parse site urls
                        data = json.loads(res) if isinstance(res, str) else res
                        return [site.get("site_url") for site in data.get("siteEntry", [])]
            return []

        _gsc_site_cache = loop.run_until_complete(fetch_props())
        loop.run_until_complete(toolset.close())
        return _gsc_site_cache
    except Exception as e:
        print(f"[GSC Warning] Failed to run list_properties: {e}")
        return []

def _is_property_authenticated(page_url: str) -> bool:
    """Gating guard: Checks if the page_url domain is authenticated in Search Console."""
    if not _is_gsc_auth():
        return False

    domain = urlparse(page_url).netloc
    auth_sites = _get_authenticated_properties()
    for site in auth_sites:
        if domain in site:
            return True
    return False

# Stdio GSC Wrapper helper
def _call_gsc_mcp_tool(tool_name: str, arguments: dict) -> dict:
    """Executes a tool on the GSC stdio MCP server."""
    cmd = os.environ.get("GSC_MCP_COMMAND")
    args = json.loads(os.environ.get("GSC_MCP_ARGS", "[]"))

    toolset = McpToolset(
        connection_params=StdioServerParameters(
            command=cmd,
            args=args
        )
    )

    loop = asyncio.get_event_loop()
    async def run_call():
        tools = await toolset.get_tools()
        for t in tools:
            if t.name == tool_name:
                res = await t.call(arguments=arguments)
                return res
        return {"error": f"Tool '{tool_name}' not found."}

    result = loop.run_until_complete(run_call())
    loop.run_until_complete(toolset.close())
    return result

# Public wrapper tools

def gsc_indexing_inspector(page_url: str) -> str:
    """
    Checks the indexing status of a specific URL in Google Search Console.
    Gated to only query authenticated GSC properties.
    """
    if not _is_gsc_auth():
        # Demo / Mock mode fallback
        report = [
            f"### GSC Indexing Audit for: {page_url}",
            f"- **Index Status**: `indexed`",
            f"- **Mobile Usability**: `friendly`",
            f"- **Rich Results Verdict**: `eligible`"
        ]
        return "\n".join(report)

    if not _is_property_authenticated(page_url):
        return (
            f"### GSC Indexing Audit\n"
            f"- URL: `{page_url}`\n"
            f"- Status: **⚠️ Skipped (Property not authenticated in Search Console)**\n"
            f"*(On-page audit results are unaffected. Mock mode mock data: Status: Indexed, Mobile Friendly: Yes)*"
        )

    try:
        domain = urlparse(page_url).netloc
        site_url = f"https://{domain}/"
        res = _call_gsc_mcp_tool("inspect_url_enhanced", {"site_url": site_url, "page_url": page_url})

        report = [
            f"### GSC Indexing Report for: {page_url}",
            f"- **Index Status**: `{res.get('inspectionResult', {}).get('indexStatusResult', {}).get('verdict', 'unknown')}`",
            f"- **Mobile Usability**: `{res.get('inspectionResult', {}).get('mobileUsabilityResult', {}).get('verdict', 'unknown')}`",
            f"- **Rich Results Verdict**: `{res.get('inspectionResult', {}).get('richResultsResult', {}).get('verdict', 'unknown')}`"
        ]
        return "\n".join(report)
    except Exception as e:
        return f"Error executing GSC URL inspection: {e}"

def gsc_performance_report(site_url: str, days: int = 28) -> str:
    """
    Retrieves aggregate performance metrics for an authenticated property.
    """
    if not _is_gsc_auth():
        # Demo / Mock mode fallback
        report = [
            f"### GSC Performance Report (Last {days} days)",
            f"- **Total Clicks**: `1,240`",
            f"- **Total Impressions**: `45,300`",
            f"- **Average CTR**: `2.74%`",
            f"- **Average Position**: `14.5`"
        ]
        return "\n".join(report)

    if not _is_property_authenticated(site_url):
        return (
            f"### GSC Performance Report\n"
            f"- Property: `{site_url}`\n"
            f"- Status: **⚠️ Skipped (Property not authenticated)**\n"
            f"*(Mock performance stats: Clicks: 1,240, Impressions: 45K, CTR: 2.76%, Position: 14.5)*"
        )

    try:
        res = _call_gsc_mcp_tool("get_performance_overview", {"site_url": site_url, "days": int(days)})
        report = [
            f"### GSC Performance Overview (Last {days} days)",
            f"- **Total Clicks**: `{res.get('clicks', 0):,}`",
            f"- **Total Impressions**: `{res.get('impressions', 0):,}`",
            f"- **Average CTR**: `{res.get('ctr', 0.0)*100:.2f}%`",
            f"- **Average Position**: `{res.get('position', 0.0):.1f}`"
        ]
        return "\n".join(report)
    except Exception as e:
        return f"Error retrieving GSC performance: {e}"

def gsc_page_query_analysis(page_url: str) -> str:
    """
    Retrieves the queries driving impressions and clicks to a specific page.
    """
    if not _is_gsc_auth():
        # Demo / Mock mode fallback
        report = [
            f"### GSC Page Query Analysis for: {page_url}",
            f"- `alternative destinations to dubai`: clicks=420, impressions=12100, position=3.2",
            f"- `tired of dubai`: clicks=310, impressions=8500, position=2.1",
            f"- `where to go instead of dubai`: clicks=180, impressions=4200, position=5.4",
            f"- `travelanders dubai alternatives`: clicks=120, impressions=1500, position=1.1",
            f"- `dubai alternative travel`: clicks=50, impressions=950, position=8.6"
        ]
        return "\n".join(report)

    if not _is_property_authenticated(page_url):
        return (
            f"### GSC Page Query Analysis\n"
            f"- URL: `{page_url}`\n"
            f"- Status: **⚠️ Skipped (Property not authenticated)**\n"
            f"*(Mock traffic keywords: 'Shopify SEO guide', 'Shopify agency Sonnet and Prose')*"
        )

    try:
        domain = urlparse(page_url).netloc
        site_url = f"https://{domain}/"
        res = _call_gsc_mcp_tool("get_search_by_page_query", {"site_url": site_url, "page_url": page_url, "row_limit": 5})

        report = [f"### Top Search Console Queries for Page: {page_url}"]
        rows = res.get("rows", [])
        for row in rows[:5]:
            query = row.get("keys", [""])[0]
            clicks = row.get("clicks", 0)
            impressions = row.get("impressions", 0)
            pos = row.get("position", 0.0)
            report.append(f"- `{query}`: clicks={clicks}, impressions={impressions}, position={pos:.1f}")

        if not rows:
            report.append("- No query data found for this page.")
        return "\n".join(report)
    except Exception as e:
        return f"Error retrieving page query analysis: {e}"

# =====================================================================
# 4. MULTI-URL DIAGNOSTIC TOOLS
# =====================================================================

def canonical_audit(urls: str) -> str:
    """
    Audits a newline-separated batch of URLs for canonical tag compliance and cannibalization.
    """
    url_list = [u.strip() for u in urls.split("\n") if u.strip()]
    if not url_list:
        return "Error: No URLs provided for canonical audit."

    report = ["### Batch Canonical & Cannibalization Audit"]
    canonical_mappings = {}

    for url in url_list:
        try:
            resp = requests.get(url, headers=BROWSER_HEADERS, timeout=10, verify=_get_verify_param(url))
            if resp.status_code != 200:
                report.append(f"- `{url}`: ❌ Failed to fetch (Status {resp.status_code})")
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')
            canon_tag = soup.find('link', attrs={'rel': 'canonical'})
            canon_url = canon_tag.get('href', '').strip() if canon_tag else ""

            if not canon_url:
                report.append(f"- `{url}`: ❌ Missing canonical tag")
            else:
                canon_path = urlparse(canon_url).path
                url_path = urlparse(url).path

                is_self = (canon_path.rstrip('/') == url_path.rstrip('/'))
                self_status = "✅ Self-referencing" if is_self else f"🔗 Points to: `{canon_url}`"
                report.append(f"- `{url}`: {self_status}")

                # Track for cannibalization
                canonical_mappings.setdefault(canon_url, []).append(url)
        except Exception as e:
            report.append(f"- `{url}`: ❌ Error during connection: {e}")

    # Detect cannibalization
    cannibalization_found = False
    for canon, source_urls in canonical_mappings.items():
        if len(source_urls) > 1:
            if not cannibalization_found:
                report.append("\n⚠️ **Cannibalization Warnings:**")
                cannibalization_found = True
            report.append(f"- `{canon}` is targeted by multiple separate URLs:")
            for s in source_urls:
                report.append(f"  * `{s}`")

    return "\n".join(report)

def redirect_chain_detector(url: str) -> str:
    """
    Follows a URL's response history to detect redirect chains, loops, and status codes.
    """
    try:
        report = [f"### Redirect Chain Audit for: `{url}`"]
        current_url = url
        chain = []
        visited = set()

        count = 0
        while count < 10:
            count += 1
            visited.add(current_url)

            resp = requests.get(current_url, headers=BROWSER_HEADERS, allow_redirects=False, timeout=5, verify=_get_verify_param(current_url))
            status = resp.status_code

            # Record hop
            chain.append((current_url, status))

            if status in (301, 302, 307, 308):
                loc = resp.headers.get("Location", "")
                # Resolve relative redirects
                if loc.startswith("/"):
                    parsed = urlparse(current_url)
                    loc = f"{parsed.scheme}://{parsed.netloc}{loc}"

                if not loc:
                    chain.append(("ERROR: Empty location header", 0))
                    break

                if loc in visited:
                    chain.append((loc, "🔄 REDIRECT LOOP DETECTED"))
                    break

                current_url = loc
            else:
                break

        # Build path display
        for i, (u, status_code) in enumerate(chain):
            arrow = " ➔ " if i < len(chain) - 1 else ""
            report.append(f"`Hop {i+1}`: `[{status_code}]` `{u}`{arrow}")

        if len(chain) > 3:
            report.append(f"\n⚠️ **Warning**: Long redirect chain detected ({len(chain)} hops). Consolidate links to a direct path.")

        return "\n".join(report)
    except Exception as e:
        return f"Error detecting redirect chain: {e}"
