import os
import sys

# Reconfigure stdout/stderr to use UTF-8 with fallback replacement to prevent Windows and server-level encoding crashes
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except Exception:
        pass

import re
import asyncio
import requests
from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.adk.workflow import Edge, Workflow, START
from dotenv import load_dotenv

# Import upgraded technical SEO auditor, SerpAPI, GSC and diagnostic tools
from app.tools.seo_tools import (
    advanced_seo_audit,
    serp_position_tracker,
    aeo_citation_checker,
    keyword_opportunity_finder,
    rich_snippet_verifier,
    gsc_indexing_inspector,
    gsc_performance_report,
    gsc_page_query_analysis,
    canonical_audit,
    redirect_chain_detector,
    require_oauth_claims,
    audit_hidden_faq_schema,
    discover_site_structure_tool,
    map_product_lines_tool
)
from app.tools.wp_client import get_wp_credentials, base_site_url
from app.tools.geo_utils import resolve_target_region

from app.tools.google_docs_native import (
    read_google_doc as read_doc,
    create_google_doc as create_doc,
    append_to_google_doc as append_doc,
    update_google_doc as update_doc,
    update_google_doc_from_file as update_doc_from_file,
    append_to_google_doc_from_file as append_doc_from_file
)


# Load local environment variables from .env if present
load_dotenv()

# Configure Project Credentials dynamically from Env (default to sandbox project if none specified)
gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "vibe-coding-assignments")
os.environ["GOOGLE_CLOUD_PROJECT"] = gcp_project
os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = os.environ.get("GOOGLE_CLOUD_QUOTA_PROJECT", gcp_project)

# Load model client securely (allow model overriding via GEMINI_MODEL)
from app.config import DEFAULT_GEMINI_MODEL
api_key = os.environ.get("GEMINI_API_KEY")
model = Gemini(model=DEFAULT_GEMINI_MODEL, api_key=api_key)

# Robust automatic retry patch for Google GenAI 503 ServerErrors and 429 Rate Limits
try:
    from tenacity import retry, stop_after_attempt, wait_exponential
    from google.genai.errors import ServerError, ClientError

    def retry_if_transient_error(exception):
        if isinstance(exception, ServerError):
            return True
        if isinstance(exception, ClientError):
            if getattr(exception, "status_code", None) == 429:
                return True
            if "429" in str(exception) or "RESOURCE_EXHAUSTED" in str(exception):
                return True
        return False

    original_generate_content_async = model.api_client.aio.models.generate_content
    original_generate_content_sync = model.api_client.models.generate_content

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_transient_error,
        reraise=True
    )
    async def retried_generate_content_async(*args, **kwargs):
        c = kwargs.get('contents') or (args[1] if len(args) > 1 else None)
        if isinstance(c, list) and len(c) > 0:
            last_chunk = c[-1]
            role = getattr(last_chunk, 'role', None)
            parts = getattr(last_chunk, 'parts', None) or []
            print(f"[*] generate_content_async: dispatched turn {len(c)-1} (role={role}, parts_len={len(parts)})")
            for j, p in enumerate(parts):
                txt = p.text[:100].replace('\n', ' ') if p.text else None
                if txt:
                    txt = txt.encode('ascii', errors='replace').decode('ascii')
                fc = p.function_call.name if p.function_call else None
                fr = p.function_response.name if p.function_response else None
                print(f"    -> Part {j}: text={txt}, function_call={fc}, function_response={fr}")
        else:
            print(f"[*] generate_content_async input contents length: {len(c) if isinstance(c, list) else 1}")

        try:
            return await original_generate_content_async(*args, **kwargs)
        except ClientError as ce:
            status_code = getattr(ce, "status_code", getattr(ce, "code", None))
            if status_code == 429 or "429" in str(ce) or "RESOURCE_EXHAUSTED" in str(ce):
                match = re.search(r"retry in (\d+\.?\d*)s", str(ce))
                delay = float(match.group(1)) + 1.0 if match else 45.0
                print(f"[!] Rate limit hit (429). Sleeping for {delay:.2f} seconds before retrying...")
                await asyncio.sleep(delay)
            raise ce

    @retry(
        stop=stop_after_attempt(6),
        wait=wait_exponential(multiplier=2, min=5, max=60),
        retry=retry_if_transient_error,
        reraise=True
    )
    def retried_generate_content_sync(*args, **kwargs):
        import time
        try:
            return original_generate_content_sync(*args, **kwargs)
        except ClientError as ce:
            status_code = getattr(ce, "status_code", getattr(ce, "code", None))
            if status_code == 429 or "429" in str(ce) or "RESOURCE_EXHAUSTED" in str(ce):
                match = re.search(r"retry in (\d+\.?\d*)s", str(ce))
                delay = float(match.group(1)) + 1.0 if match else 45.0
                print(f"[!] Rate limit hit (429). Sleeping for {delay:.2f} seconds before retrying...")
                time.sleep(delay)
            raise ce

    model.api_client.aio.models.generate_content = retried_generate_content_async
    model.api_client.models.generate_content = retried_generate_content_sync
except Exception as e:
    print(f"[*] Warning: Failed to apply retry patch to model: {e}")



def audit_brand_aeo_visibility(brand_name: str, search_query: str, gl: str = "us", hl: str = "en") -> str:
    """
    Queries Google via SerpAPI and parses listings
    to calculate Share of Model (SoM) and cite occurrences.
    """
    serpapi_key = os.environ.get("SERPAPI_API_KEY")

    # MOCK MODE: Use simulated results if no SerpAPI credentials are set
    if not serpapi_key:
        print("[*] SerpAPI key missing. Running audit_brand_aeo_visibility in mock mode.")
        mock_results = [
            {"title": "Best Shopify SEO Agencies in 2026", "snippet": "Sonnet and Prose is widely regarded as a top eCommerce SEO agency for Shopify stores.", "link": "https://clutch.co/seo-agencies/shopify"},
            {"title": "Shopify Marketing Experts Guide", "snippet": "Optimize your Shopify store using top marketing agencies like Sonnet and Prose.", "link": "https://shopify.com/blog/experts-list"},
            {"title": "Organic Search Experts", "snippet": "A listing of search specialists globally.", "link": "https://moz.com/seo-list"},
            {"title": "How to scale your Shopify traffic", "snippet": "Tips and strategies for scaling organic traffic.", "link": "https://searchengineland.com/shopify-tips"}
        ]
        organic_list = mock_results
        ai_overview = {}
    else:
        # Resolve geotargeting
        if gl == "us":
            gl_resolved, location_resolved = resolve_target_region(search_query)
        else:
            gl_resolved, location_resolved = gl, None

        try:
            search_params = {
                "q": search_query,
                "api_key": serpapi_key,
                "engine": "google",
                "gl": gl_resolved,
                "hl": hl
            }
            if location_resolved:
                search_params["location"] = location_resolved

            # Query SerpAPI with standard parameters
            response = requests.get(
                "https://serpapi.com/search",
                params=search_params,
                timeout=10
            )
            if response.status_code != 200:
                return f"Error: Failed to fetch search results from SerpAPI (Status: {response.status_code})."

            data = response.json()
            organic_list = data.get("organic_results", [])
            ai_overview = data.get("ai_overview", {})
            page_token = ai_overview.get("page_token")
            if page_token:
                try:
                    ai_resp = requests.get(
                        "https://serpapi.com/search",
                        params={
                            "engine": "google_ai_overview",
                            "page_token": page_token,
                            "api_key": serpapi_key
                        },
                        timeout=10
                    )
                    if ai_resp.status_code == 200:
                        ai_overview = ai_resp.json().get("ai_overview", ai_resp.json())
                except Exception as e:
                    print(f"[!] Warning: Failed to retrieve lazy-loaded AI Overview in visibility check: {e}")
        except Exception as e:
            return f"Error: Failed to connect to SerpAPI: {e}"

    citations = []
    scanned_items = []
    from urllib.parse import urlparse

    # 1. Parse Organic Results
    for item in organic_list:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        if not link:
            continue
        scanned_items.append(link)

        domain = urlparse(link).netloc.lower()
        if (re.search(rf"\b{re.escape(brand_name)}\b", title + " " + snippet, re.IGNORECASE) or
                brand_name.lower() in domain):
            citations.append(link)

    # 2. Parse AI Overview references
    for ref in ai_overview.get("references", []):
        title = ref.get("title", "")
        snippet = ref.get("snippet", "")
        link = ref.get("link", "")
        if not link:
            continue
        scanned_items.append(link)

        domain = urlparse(link).netloc.lower()
        if (re.search(rf"\b{re.escape(brand_name)}\b", title + " " + snippet, re.IGNORECASE) or
                brand_name.lower() in domain):
            citations.append(link)

    # Parse AI Overview direct links
    for l_obj in ai_overview.get("links", []):
        link = l_obj.get("link", "")
        if not link:
            continue
        scanned_items.append(link)

        domain = urlparse(link).netloc.lower()
        if brand_name.lower() in domain:
            citations.append(link)

    # Deduplicate while preserving order
    seen_scanned = set()
    scanned_items = [x for x in scanned_items if not (x in seen_scanned or seen_scanned.add(x))]
    seen_citations = set()
    citations = [x for x in citations if not (x in seen_citations or seen_citations.add(x))]

    total_listings = len(scanned_items)
    som = (len(citations) / total_listings * 100) if total_listings > 0 else 0

    report = [
        f"### AEO Citation Audit for Brand: {brand_name}",
        f"**Search Query**: '{search_query}'",
        f"**Total Listings Scanned**: {total_listings}",
        f"**Brand Citations Found**: {len(citations)}",
        f"**Share of Model (SoM)**: {som:.1f}%",
        "\n**🔗 Citations List:**"
    ]

    if citations:
        for url in citations:
            report.append(f"- {url}")
    else:
        report.append("- No brand citations found for this query.")

    return "\n".join(report)

@require_oauth_claims("site:write")
def inject_aeo_schema_metafield(wp_post_id: int, schema_type: str, schema_json: str, tool_context=None) -> str:
    """
    Pushes generated FAQ or local schema JSON-LD back into a WordPress post's custom meta fields.
    """
    wp_url, wp_user, wp_pass, is_mock = get_wp_credentials()
    resolved_id = int(wp_post_id)

    # MOCK MODE: Simulate success if credentials are not configured yet or during tests
    if is_mock:
        print("[*] WordPress credentials missing or in test mode. Running inject_aeo_schema_metafield in mock mode.")
        return f"Success: (MOCKED) Injected {schema_type} JSON-LD Schema into WordPress Post #{resolved_id} metadata."

    try:
        # POST request to update post meta in WordPress REST API (try posts endpoint first)
        response = requests.post(
            f"{wp_url}/posts/{resolved_id}",
            auth=(wp_user, wp_pass),
            json={
                "meta": {
                    "aeo_schema_json": schema_json,
                    "aeo_schema_type": schema_type
                }
            },
            timeout=10
        )

        # If 404/not found or 405 not allowed, try pages endpoint
        if response.status_code in (404, 405):
            response = requests.post(
                f"{wp_url}/pages/{resolved_id}",
                auth=(wp_user, wp_pass),
                json={
                    "meta": {
                        "aeo_schema_json": schema_json,
                        "aeo_schema_type": schema_type
                    }
                },
                timeout=10
            )

        if response.status_code == 200:
            return f"Success: Injected {schema_type} JSON-LD Schema into WordPress Post/Page #{resolved_id} metadata."
        else:
            return f"Error: WordPress REST API rejected schema update (Status: {response.status_code}, Msg: {response.text})."
    except Exception as e:
        return f"Error: Failed to connect to WordPress during schema injection: {e}"

@require_oauth_claims("site:write")
def publish_gutenberg_page(title: str, content_html: str, status: str = "draft", tool_context=None) -> str:
    """
    Creates or updates a WordPress page using raw Gutenberg HTML block markup.

    Args:
        title: The title of the page or post.
        content_html: The complete HTML markup containing Gutenberg block comments.
        status: The publishing status, e.g., 'draft' or 'publish'. Default is 'draft'.

    Returns:
        A success or error message containing the created post/page ID.
    """
    wp_url, wp_user, wp_pass, is_mock = get_wp_credentials()

    # MOCK MODE: Simulate success if credentials are not configured yet or during tests
    if is_mock:
        print("[*] WordPress credentials missing or in test mode. Running publish_gutenberg_page in mock mode.")
        return f"Success: (MOCKED) Created draft page '{title}' successfully with Gutenberg content."

    try:
        response = requests.post(
            f"{wp_url}/pages",
            auth=(wp_user, wp_pass),
            json={
                "title": title,
                "content": content_html,
                "status": status
            },
            timeout=10
        )
        if response.status_code == 201:
            data = response.json()
            post_id = data.get("id")
            slug = data.get("slug")
            if not slug:
                slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')

            base_url = base_site_url(wp_url)
            pretty_link = f"{base_url}/{slug}/"
            edit_link = f"{base_url}/wp-admin/post.php?post={post_id}&action=edit"

            return (
                f"Success: Published Gutenberg page '{title}'!\n"
                f"- Page ID: {post_id}\n"
                f"- Permanent Slug URL: {pretty_link}\n"
                f"- Edit Dashboard Link: {edit_link}"
            )
        else:
            return f"Error: WordPress REST API rejected page creation (Status: {response.status_code}, Msg: {response.text})."
    except Exception as e:
        return f"Error: Failed to connect to WordPress during page creation: {e}"

# Configure Gutenberg AEO Copilot Agent & Workflow
aeo_copilot_agent = LlmAgent(
    name="GutenbergAeoCopilot",
    model=model,
    mode="chat",
    instruction=(
        "You are an expert digital marketing agent for Sonnet and Prose.\n"
        "Your capabilities include:\n"
        "1. Auditing Gutenberg WordPress posts for 19 technical SEO and AEO guidelines (headings, social tags, image alt/dimensions/lazyload, links) using 'advanced_seo_audit'.\n"
        "2. Running organic search position tracking and AEO citation/Share of Model audits using SerpAPI tools.\n"
        "3. Inspecting Google Search Console indexing, overall query/CTR performance metrics, and query-page mapping for verified properties.\n"
        "4. Running bulk canonical checks for cannibalization and tracing redirect loops/chains.\n"
        "5. Injecting schema metadata back into WordPress post/page metafields.\n"
        "6. Publishing new Gutenberg pages using native blocks or custom React blocks based on user prompt.\n"
        "7. Mapping website top-level directories/subdomains and identifying product lines without deep crawling using 'discover_site_structure_tool' and 'map_product_lines_tool'.\n\n"
        "Geotargeting & Search Localization Guidelines:\n"
        "- When invoking organic search position tracking, visibility, or citation audit tools, you should ensure search results reflect the correct geographical target (e.g. use gl='ng' and hl='en' for searches targeting Nigeria, or 'uk' and 'en' for United Kingdom focus).\n\n"
        "Structured Data & Schema Rules:\n"
        "- Suggest appropriate structured data types matching the page intent (e.g., Article, Product, Review, LocalBusiness) by referencing Google's official Search Gallery: https://developers.google.com/search/docs/appearance/structured-data/search-gallery.\n"
        "- Avoid listing, discussing, or explaining irrelevant or non-applicable schema types in your reports.\n"
        "- Authoritative Reference Retrieval: To ensure recommendations align with the latest Google Core Updates and Search Console guidelines, utilize the 'google-developer-knowledge' MCP server tools ('search_documents' or 'answer_query') to retrieve live documentation when validating search features.\n\n"
        "Formatting Guidelines:\n"
        "- DO NOT use standard markdown tables (e.g. '| Header | Header |'). Telegram does not render markdown tables, which results in broken, unreadable text layout.\n"
        "- Instead, format all tabular data using a preformatted code block with fixed-width space alignment to ensure perfectly clean columns, like this:\n"
        "  ```text\n"
        "  Query                      Clicks   Imps     CTR      Pos\n"
        "  ---------------------------------------------------------\n"
        "  alternative dest to dubai  420      12,100   3.47%    3.2\n"
        "  ```\n"
        "- Strict Audit Reporting: When presenting the results of 'advanced_seo_audit', you MUST report the errors, warnings, and metrics verbatim as returned by the tool. DO NOT add, remove, or modify any listed Critical Errors or Technical Warnings (such as claiming a canonical tag is missing when the tool lists it as passed/self-referential).\n\n"
        "When publishing or updating pages:\n"
        "- Choose between native and custom blocks using your Decision Matrix:\n"
        "  * Use native blocks (e.g. core/heading, core/paragraph, core/list, core/image) for standard text and layouts.\n"
        "  * Use custom blocks (e.g. 'aeo-custom-blocks/hero' or 'aeo-custom-blocks/faq') for high-converting elements.\n"
        "- Generate the complete block HTML comments correctly:\n"
        "  * Hero block format (MUST include alignment for full-width layout):\n"
        "    <!-- wp:aeo-custom-blocks/hero {\"align\":\"full\",\"title\":\"...\",\"subtitle\":\"...\",\"ctaText\":\"...\",\"ctaUrl\":\"...\"} -->\n"
        "    <div class=\"wp-block-aeo-hero alignfull\"><header class=\"aeo-hero-header\"><h1>...</h1><p class=\"aeo-hero-subtitle\">...</p><div class=\"aeo-hero-cta\"><a href=\"...\" class=\"aeo-hero-cta-btn\">...</a></div></header></div>\n"
        "    <!-- /wp:aeo-custom-blocks/hero -->\n"
        "  * FAQ block format:\n"
        "    <!-- wp:aeo-custom-blocks/faq {\"question\":\"...\",\"answer\":\"...\"} -->\n"
        "    <details class=\"wp-block-aeo-faq\"><summary>...</summary><div class=\"aeo-faq-answer-content\">...</div></details>\n"
        "    <!-- /wp:aeo-custom-blocks/faq -->\n"
        "- Call the 'publish_gutenberg_page' tool to create the page in WordPress."
    ),
    tools=[
        advanced_seo_audit,
        serp_position_tracker,
        aeo_citation_checker,
        keyword_opportunity_finder,
        rich_snippet_verifier,
        gsc_indexing_inspector,
        gsc_performance_report,
        gsc_page_query_analysis,
        canonical_audit,
        redirect_chain_detector,
        audit_brand_aeo_visibility,
        inject_aeo_schema_metafield,
        publish_gutenberg_page,
        audit_hidden_faq_schema,
        discover_site_structure_tool,
        map_product_lines_tool,
        read_doc,
        create_doc,
        append_doc,
        update_doc,
        update_doc_from_file,
        append_doc_from_file
    ]
)

root_agent = Workflow(
    name="aeo_copilot_workflow",
    edges=[Edge(from_node=START, to_node=aeo_copilot_agent)]
)
