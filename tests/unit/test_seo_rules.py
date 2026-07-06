import pytest
from app.tools.audit_rules import run_audit
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
    redirect_chain_detector
)

def test_individual_audit_rules():
    # Construct a bad HTML content to trigger warnings/errors
    bad_html = """<!DOCTYPE html>
    <html>
    <head>
        <title>Short</title>
        <!-- Missing description, OG, Twitter Cards, Canonical -->
    </head>
    <body>
        <h1>Duplicate H1</h1>
        <h1>Duplicate H1</h1>
        <h2>Heading Skip followed directly by H4</h2>
        <h4>Invalid H4</h4>
        <h3>Empty below</h3>
        <h2></h2>
        <p>Short content.</p>
        <img src="http://example.com/logo.png" loading="lazy" />
        <a href="/next">Click here</a>
    </body>
    </html>"""

    results = run_audit(bad_html, page_url="http://example.com/page/")

    # Assertions on rule failures
    errors = "\n".join(results["errors"])
    warnings = "\n".join(results["warnings"])

    # 1. Meta Title is too short
    assert "Meta Title" in errors or "Meta Title" in warnings
    # 2. Meta Description is missing
    assert "Meta Description" in errors
    # 3. Canonical URL is missing
    assert "Canonical URL" in errors
    # 4. H1 tag count has duplicate
    assert "H1 Tag Count" in errors
    # 5. Heading Hierarchy skipped level H2->H4
    assert "Heading Hierarchy" in warnings
    # 6. Empty heading exists
    assert "Empty Headings" in warnings
    # 7. Thin content check word count < 300
    assert "Thin Content Check" in errors
    # 8. First image lazyloaded
    assert "First Image Lazyload" in warnings
    # 9. Generic anchor text "Click here"
    assert "Generic Anchor Text" in warnings
    # 10. Image missing alt and dimensions
    assert "Image Alt Text" in warnings
    assert "Image Dimensions" in warnings

def test_advanced_seo_audit_mock(monkeypatch):
    # Force Mock Mode
    monkeypatch.delenv("WP_API_URL", raising=False)
    monkeypatch.delenv("WP_USERNAME", raising=False)
    monkeypatch.delenv("WP_APPLICATION_PASSWORD", raising=False)

    report = advanced_seo_audit("123")
    assert "SEO & AEO Audit Summary" in report
    assert "Word Count" in report
    assert "Critical Errors" in report
    assert "Technical Warnings" in report

def test_serp_tools_mock(monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)

    track_res = serp_position_tracker("http://aeo-copilot.local", "seo agency")
    assert "SERP Position Tracker" in track_res

    citation_res = aeo_citation_checker("seo agency", "http://aeo-copilot.local")
    assert "AEO Citation Report" in citation_res

    kw_res = keyword_opportunity_finder("seo")
    assert "Keyword Autocomplete Opportunities" in kw_res

    snippet_res = rich_snippet_verifier("seo")
    assert "Rich Snippet Verification" in snippet_res

def test_gsc_tools_mock(monkeypatch):
    monkeypatch.delenv("GSC_MCP_COMMAND", raising=False)

    idx_res = gsc_indexing_inspector("http://example.com")
    assert "GSC Indexing Audit" in idx_res

    perf_res = gsc_performance_report("http://example.com")
    assert "GSC Performance Report" in perf_res

    query_res = gsc_page_query_analysis("http://example.com")
    assert "GSC Page Query Analysis" in query_res

def test_diagnostic_tools_mock():
    # Test redirect chain with a direct non-redirect url
    chain_res = redirect_chain_detector("https://httpbin.org/status/200")
    assert "Hop 1" in chain_res

def test_oauth_claims_gate(monkeypatch):
    import jwt
    import datetime
    from app.agent import inject_aeo_schema_metafield
    from app.tools.seo_tools import set_user_session

    # 1. Setup dev key env
    monkeypatch.setenv("DEVELOPER_SECRET_KEY", "super_secret_test_key")

    # Define a helper ToolContext class
    class MockToolContext:
        def __init__(self, user_id):
            self.user_id = user_id

    ctx = MockToolContext("user_abc")

    # 2. Test local dev bypass (should succeed and run the mocked tool directly)
    res_local = inject_aeo_schema_metafield(wp_post_id=18, schema_type="FAQ", schema_json="{}", tool_context=ctx)
    assert "Success" in res_local

    # 3. Test non-local URL without token (should require authentication)
    # Temporarily remove WP_API_URL so it attempts to treat the post_id as non-local or uses mock
    monkeypatch.setenv("WP_API_URL", "https://production-site.com/wp-json/wp/v2")
    res_unauth = inject_aeo_schema_metafield(wp_post_id=18, schema_type="FAQ", schema_json="{}", tool_context=ctx)
    assert "Authentication required" in res_unauth

    # 4. Test invalid token
    set_user_session("user_abc", "invalid_jwt_token_string")
    res_invalid = inject_aeo_schema_metafield(wp_post_id=18, schema_type="FAQ", schema_json="{}", tool_context=ctx)
    assert "Invalid authentication token" in res_invalid

    # 5. Test valid token with insufficient scope
    payload_no_scope = {
        "sub": "user_abc",
        "scopes": ["some:other:scope"],
        "verified_properties": ["https://production-site.com"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token_no_scope = jwt.encode(payload_no_scope, "super_secret_test_key", algorithm="HS256")
    set_user_session("user_abc", token_no_scope)
    res_no_scope = inject_aeo_schema_metafield(wp_post_id=18, schema_type="FAQ", schema_json="{}", tool_context=ctx)
    assert "Insufficient permissions" in res_no_scope

    # 6. Test valid token with missing domain ownership
    payload_bad_domain = {
        "sub": "user_abc",
        "scopes": ["site:write"],
        "verified_properties": ["https://unrelated-domain.com"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token_bad_domain = jwt.encode(payload_bad_domain, "super_secret_test_key", algorithm="HS256")
    set_user_session("user_abc", token_bad_domain)
    res_bad_domain = inject_aeo_schema_metafield(wp_post_id=18, schema_type="FAQ", schema_json="{}", tool_context=ctx)
    assert "Access Denied" in res_bad_domain

    # 7. Test valid token with correct scope and domain ownership
    # Restore dummy credentials so the tool executes requests instead of local dev bypass mock
    monkeypatch.setenv("WP_API_URL", "https://production-site.com/wp-json/wp/v2")
    monkeypatch.setenv("WP_USERNAME", "admin")
    monkeypatch.setenv("WP_APPLICATION_PASSWORD", "secret")

    payload_ok = {
        "sub": "user_abc",
        "scopes": ["site:write"],
        "verified_properties": ["https://production-site.com"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    token_ok = jwt.encode(payload_ok, "super_secret_test_key", algorithm="HS256")
    set_user_session("user_abc", token_ok)

    # Mock requests.post to avoid real network hit
    import requests
    class MockResponse:
        status_code = 200

    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: MockResponse())

    res_ok = inject_aeo_schema_metafield(wp_post_id=18, schema_type="FAQ", schema_json="{}", tool_context=ctx)
    assert "Success" in res_ok

def test_image_optimization_rules():
    # Construct an HTML with failing cases for all new image rules
    html = """<!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta property="og:image:width" content="150" /> <!-- Rule 26: dimension below 200 -->
        <meta property="og:image:height" content="150" />
        <meta name="twitter:card" content="summary_large_image" />
    </head>
    <body>
        <!-- Rule 22: First image is LCP candidate, lacks fetchpriority and eager loading -->
        <!-- Rule 20: Legacy format (png) with no picture fallback -->
        <!-- Rule 21: Missing srcset/sizes responsive hints -->
        <!-- Rule 23: Non-descriptive filename (8 hex characters) -->
        <img src="/assets/a3f8b2c1.png" width="400" height="300" />
        
        <!-- Rule 25: Decorative image (icon) with verbose alt text > 3 words -->
        <img src="/icons/chevron.png" alt="This is a simple chevron icon pointing right" width="24" height="24" />
        
        <!-- Rule 24: Image not wrapped in figure + figcaption -->
        <img src="/images/eportfolio-dashboard.png" alt="Dashboard" width="800" height="600" />
        
        <!-- Rule 25: SVG without role="img" or labels -->
        <svg height="100" width="100">
          <circle cx="50" cy="50" r="40" stroke="black" stroke-width="3" fill="red" />
        </svg>
    </body>
    </html>"""

    results = run_audit(html, page_url="http://example.com/page/")

    errors = "\n".join(results["errors"])
    warnings = "\n".join(results["warnings"])

    assert "Image Format" in warnings
    assert "Responsive Images" in warnings
    assert "LCP Image Priority" in warnings
    assert "Image Filename Semantics" in warnings
    assert "Figure Semantic Wrapping" in warnings
    assert "Decorative Image Classification" in warnings
    assert "Social Image Dimensions" in warnings

def test_schema_type_awareness():
    # 1. Test page with Organization and FAQPage schema (commercial intent)
    html_commercial = """<!DOCTYPE html>
    <html>
    <head>
        <title>Commercial SaaS Page</title>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@graph": [
            {
              "@type": "Organization",
              "name": "Digication"
            },
            {
              "@type": "FAQPage",
              "mainEntity": []
            }
          ]
        }
        </script>
    </head>
    <body>
        <h1>Assessment</h1>
    </body>
    </html>"""

    results = run_audit(html_commercial, page_url="http://example.com/", intent="commercial")
    warnings_comm = "\n".join(results["warnings"])
    
    # Should flag Product/SoftwareApplication as missing, FAQPage as deprecated
    assert "FAQPage" in results["metrics"]["schema_types_deprecated"]
    assert "SoftwareApplication" in results["metrics"]["schema_types_missing"]

    # 2. Test page with Article schema (informational intent)
    html_info = """<!DOCTYPE html>
    <html>
    <head>
        <title>Informational Blog</title>
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Article",
          "headline": "How ePortfolio assessment works"
        }
        </script>
    </head>
    <body>
        <h1>How ePortfolio assessment works</h1>
    </body>
    </html>"""

    results = run_audit(html_info, page_url="http://example.com/", intent="informational")
    assert "Article" in results["metrics"]["schema_types_present"]
    assert "Product" not in results["metrics"]["schema_types_missing"]

