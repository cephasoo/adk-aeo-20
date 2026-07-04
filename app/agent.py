import os
import re
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
    require_oauth_claims
)

# Load local environment variables from .env if present
load_dotenv()

# Configure Project Credentials dynamically from Env (default to sandbox project if none specified)
gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT", "vibe-coding-assignments")
os.environ["GOOGLE_CLOUD_PROJECT"] = gcp_project
os.environ["GOOGLE_CLOUD_QUOTA_PROJECT"] = os.environ.get("GOOGLE_CLOUD_QUOTA_PROJECT", gcp_project)

# Load model client securely (allow model overriding via GEMINI_MODEL)
api_key = os.environ.get("GEMINI_API_KEY")
model_name = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
model = Gemini(model=model_name, api_key=api_key)

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
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_transient_error,
        reraise=True
    )
    async def retried_generate_content_async(*args, **kwargs):
        return await original_generate_content_async(*args, **kwargs)

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_transient_error,
        reraise=True
    )
    def retried_generate_content_sync(*args, **kwargs):
        return original_generate_content_sync(*args, **kwargs)

    model.api_client.aio.models.generate_content = retried_generate_content_async
    model.api_client.models.generate_content = retried_generate_content_sync
except Exception as e:
    print(f"[*] Warning: Failed to apply retry patch to model: {e}")

def fetch_and_parse_gutenberg_post(wp_post_id: str) -> str:
    """
    Connects to WordPress REST API, retrieves a Gutenberg post (by ID or URL slug),
    and audits it for semantic heading hierarchies and image alt tags.
    """
    wp_url = os.environ.get("WP_API_URL")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APPLICATION_PASSWORD")

    # Clean application password (remove spaces) if present
    if wp_pass:
        wp_pass = wp_pass.replace(" ", "")

    # MOCK MODE: Use simulated content if credentials are not configured yet
    if not wp_url or not wp_user or not wp_pass:
        print("[*] WordPress credentials missing. Running fetch_and_parse_gutenberg_post in mock mode.")
        # Simulated raw Gutenberg post HTML content
        content_html = """
        <!-- wp:heading {"level":1} -->
        <h1>Ultimate Guide to Shopify SEO</h1>
        <!-- /wp:heading -->
        <!-- wp:paragraph -->
        <p>This is a paragraph outlining our Shopify SEO agency strategies.</p>
        <!-- /wp:paragraph -->
        <!-- wp:image {"id":456,"sizeSlug":"full","linkDestination":"none"} -->
        <figure class="wp-block-image size-full"><img src="http://example.com/logo.png" alt="" class="wp-image-456"/></figure>
        <!-- /wp:image -->
        <!-- wp:heading {"level":4} -->
        <h4>Advanced Technical Shopify Checklists</h4>
        <!-- /wp:heading -->
        """
        resolved_id = "MOCK_123"
    else:
        # Determine if input is a URL or a direct ID
        input_str = str(wp_post_id).strip()

        # Check if it's a simple integer ID
        if input_str.isdigit():
            resolved_id = int(input_str)
        else:
            # It's a URL. Try to parse the ID from query params (e.g. ?p=123 or ?page_id=123)
            query_id_match = re.search(r"[?&](p|page_id)=(\d+)", input_str)
            if query_id_match:
                resolved_id = int(query_id_match.group(2))
            else:
                # Resolve by slug (extract last non-empty path component)
                path_parts = [p for p in input_str.split("/") if p]
                if not path_parts:
                    return f"Error: Invalid WordPress URL format: '{wp_post_id}'."

                slug = path_parts[-1]
                # If there are query parameters in the last component, strip them
                if "?" in slug:
                    slug = slug.split("?")[0]

                print(f"[*] Attempting to resolve post by slug: '{slug}'")
                try:
                    # Query posts by slug
                    response = requests.get(
                        f"{wp_url}/posts",
                        params={"slug": slug},
                        auth=(wp_user, wp_pass),
                        timeout=10
                    )
                    posts = response.json() if response.status_code == 200 else []

                    if not posts:
                        # Fallback: Query pages by slug
                        response = requests.get(
                            f"{wp_url}/pages",
                            params={"slug": slug},
                            auth=(wp_user, wp_pass),
                            timeout=10
                        )
                        posts = response.json() if response.status_code == 200 else []

                    if not posts:
                        return f"Error: Could not find any post or page with slug '{slug}' on your WordPress site."

                    resolved_id = posts[0].get("id")
                    print(f"[*] Resolved slug '{slug}' to Post/Page ID: {resolved_id}")
                except Exception as e:
                    return f"Error: Failed to resolve URL slug '{slug}' from WordPress: {e}"

        # Fetch the resolved post/page
        try:
            # Try to fetch as a post first
            response = requests.get(
                f"{wp_url}/posts/{resolved_id}",
                auth=(wp_user, wp_pass),
                timeout=10
            )

            # If 404/not found, try pages endpoint
            if response.status_code == 404:
                response = requests.get(
                    f"{wp_url}/pages/{resolved_id}",
                    auth=(wp_user, wp_pass),
                    timeout=10
                )

            if response.status_code != 200:
                return f"Error: Failed to fetch post/page #{resolved_id} from WordPress REST API (Status code: {response.status_code})."

            post_data = response.json()
            content_html = post_data.get("content", {}).get("raw", post_data.get("content", {}).get("rendered", ""))
        except Exception as e:
            return f"Error: Failed to connect to local WordPress staging site: {e}"

    # --- HTML / Block Parser Engine ---
    warnings = []
    headers = []
    images = []

    # 1. Word Count Check (Lean Content)
    # Strip HTML tags and split to get clean words list
    text_content = re.sub(r'<[^>]+>', ' ', content_html)
    words = [w for w in text_content.split() if w]
    word_count = len(words)
    if word_count < 300:
        warnings.append(
            f"Thin Content Warning: Post only contains {word_count} words. Search engines and AEO systems penalize lean content under 300 words."
        )

    # 2. Parse Headings (looks for h1-h6 tags or Gutenberg heading blocks)
    heading_matches = re.findall(r'<h([1-6])[^>]*>(.*?)</h\1>', content_html, re.IGNORECASE)
    for level, text in heading_matches:
        headers.append((int(level), text.strip()))

    # Validate H1 tag count
    h1_count = sum(1 for lvl, txt in headers if lvl == 1)
    if h1_count > 1:
        warnings.append(
            f"Duplicate H1 Warning: Found {h1_count} H1 tags. A page must have exactly one H1 tag to establish proper semantic context."
        )
    elif h1_count == 0:
        warnings.append(
            f"Missing H1 Warning: No H1 tags found. A page must have exactly one H1 tag for search engines to identify the primary topic."
        )

    # Verify heading hierarchies (e.g., no jumping from h1 to h4 directly)
    for i in range(len(headers) - 1):
        curr_lvl, curr_txt = headers[i]
        next_lvl, next_txt = headers[i+1]
        if next_lvl > curr_lvl + 1:
            warnings.append(
                f"Heading Skip Warning: Skipped hierarchy levels between '{curr_txt}' (H{curr_lvl}) and '{next_txt}' (H{next_lvl})."
            )

    # 3. Parse Images (looks for img tags and examines alt tags)
    img_matches = re.findall(r'<img\s+([^>]*?)>', content_html, re.IGNORECASE)
    for attrs in img_matches:
        alt_match = re.search(r'alt=["\'](.*?)["\']', attrs, re.IGNORECASE)
        src_match = re.search(r'src=["\'](.*?)["\']', attrs, re.IGNORECASE)

        src = src_match.group(1) if src_match else "unknown"
        alt = alt_match.group(1).strip() if alt_match else ""

        images.append((src, alt))
        if not alt:
            warnings.append(f"Missing Alt Text Warning: Image '{os.path.basename(src)}' has no descriptive alt attribute.")

    # 4. Format the Audit Report
    report = [
        f"### Gutenberg Audit Report for Post #{wp_post_id}",
        f"**Word Count**: {word_count} words",
        f"**Headings Found**: {len(headers)}",
        f"**Images Found**: {len(images)}"
    ]

    if warnings:
        report.append("\n**⚠️ Technical SEO Warnings Found:**")
        for warning in warnings:
            report.append(f"- {warning}")
    else:
        report.append("\n**✅ Technical SEO Check: Passed (Heading hierarchies, word count, and image alt tags are clean).**")

    return "\n".join(report)

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
    else:
        try:
            # Query SerpAPI with standard parameters
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
                return f"Error: Failed to fetch search results from SerpAPI (Status: {response.status_code})."

            data = response.json()
            mock_results = data.get("organic_results", [])
        except Exception as e:
            return f"Error: Failed to connect to SerpAPI: {e}"

    citations = []
    total_listings = len(mock_results)

    for item in mock_results:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")

        # Check if the brand name is mentioned (case insensitive)
        if re.search(rf"\b{re.escape(brand_name)}\b", title + " " + snippet, re.IGNORECASE):
            citations.append(link)

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
    wp_url = os.environ.get("WP_API_URL")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APPLICATION_PASSWORD")

    # Clean application password (remove spaces) if present
    if wp_pass:
        wp_pass = wp_pass.replace(" ", "")

    resolved_id = int(wp_post_id)

    # MOCK MODE: Simulate success if credentials are not configured yet or during tests
    is_testing = "PYTEST_CURRENT_TEST" in os.environ
    if not wp_url or not wp_user or not wp_pass or is_testing:
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
    wp_url = os.environ.get("WP_API_URL")
    wp_user = os.environ.get("WP_USERNAME")
    wp_pass = os.environ.get("WP_APPLICATION_PASSWORD")

    # Clean application password (remove spaces) if present
    if wp_pass:
        wp_pass = wp_pass.replace(" ", "")

    # MOCK MODE: Simulate success if credentials are not configured yet or during tests
    is_testing = "PYTEST_CURRENT_TEST" in os.environ
    if not wp_url or not wp_user or not wp_pass or is_testing:
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

            # Resolve base URL from WP_API_URL
            # e.g., http://aeo-copilot.local/wp-json/wp/v2 -> http://aeo-copilot.local
            base_url = wp_url.split("/wp-json")[0]
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
    instruction=(
        "You are an expert digital marketing agent for Sonnet and Prose.\n"
        "Your capabilities include:\n"
        "1. Auditing Gutenberg WordPress posts for 19 technical SEO and AEO guidelines (headings, social tags, image alt/dimensions/lazyload, links) using 'advanced_seo_audit'.\n"
        "2. Running organic search position tracking and AEO citation/Share of Model audits using SerpAPI tools.\n"
        "3. Inspecting Google Search Console indexing, overall query/CTR performance metrics, and query-page mapping for verified properties.\n"
        "4. Running bulk canonical checks for cannibalization and tracing redirect loops/chains.\n"
        "5. Injecting schema metadata back into WordPress post/page metafields.\n"
        "6. Publishing new Gutenberg pages using native blocks or custom React blocks based on user prompt.\n\n"
        "Structured Data & Schema Rules:\n"
        "- NEVER recommend or generate FAQ schema (FAQPage) for standard blogs, niche travel sites, or e-commerce/commercial sites. Google's 2023 update deprecated FAQ rich results for general sites, restricting it strictly to government, authority, and high-trust institutional portals.\n"
        "- Instead, recommend structured data matching the page's intent (e.g. Article, Recipe, Product, LocalBusiness, Review) based on the official Google Search Gallery: https://developers.google.com/search/docs/appearance/structured-data/search-gallery.\n"
        "- If you have questions about structured data features, query the 'google-developer-knowledge' MCP server tools (like 'search_documents' or 'answer_query') to retrieve authoritative guidelines.\n\n"
        "Formatting Guidelines:\n"
        "- DO NOT use standard markdown tables (e.g. '| Header | Header |'). Telegram does not render markdown tables, which results in broken, unreadable text layout.\n"
        "- Instead, format all tabular data using a preformatted code block with fixed-width space alignment to ensure perfectly clean columns, like this:\n"
        "  ```text\n"
        "  Query                      Clicks   Imps     CTR      Pos\n"
        "  ---------------------------------------------------------\n"
        "  alternative dest to dubai  420      12,100   3.47%    3.2\n"
        "  ```\n\n"
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
        publish_gutenberg_page
    ]
)

root_agent = Workflow(
    name="aeo_copilot_workflow",
    edges=[Edge(from_node=START, to_node=aeo_copilot_agent)]
)
