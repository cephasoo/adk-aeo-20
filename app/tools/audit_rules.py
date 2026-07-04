import re
import os
from urllib.parse import urlparse

# Attempt to import BeautifulSoup, fallback to dummy or basic parser if not installed
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

def check_semantic_alignment(h1: str, headings: list) -> tuple[float, str]:
    """
    Evaluates semantic coherence between the H1 title and subheadings.
    If running under tests or API keys are missing, falls back to keyword overlap.
    Otherwise, invokes Gemini to check true semantic support.
    """
    # 1. Fallback / Keyword Overlap Calculation
    h1_words = set(re.sub(r'[^a-zA-Z0-9\s]', '', h1).lower().split())
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "is", "are", "of", "to", "your", "our", "my", "we", "how"}
    h1_keywords = h1_words - stop_words

    subheadings_text = " ".join([txt for lvl, txt in headings if lvl > 1])
    sub_words = set(re.sub(r'[^a-zA-Z0-9\s]', '', subheadings_text).lower().split())
    sub_keywords = sub_words - stop_words

    fallback_score = 0.0
    if h1_keywords:
        matching_keywords = h1_keywords.intersection(sub_keywords)
        fallback_score = (len(matching_keywords) / len(h1_keywords)) * 100

    # 2. Check if we should use fallback (offline, missing keys, or running tests)
    is_testing = "PYTEST_CURRENT_TEST" in os.environ
    api_key = os.environ.get("GEMINI_API_KEY")
    if is_testing or not api_key:
        return fallback_score, f"Keyword matching: {fallback_score:.1f}% subheading overlap."

    # 3. Live Gemini Semantic Check
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

        subheadings_list = [txt for lvl, txt in headings if lvl > 1]
        if not h1_keywords or not subheadings_list:
            return 100.0, "No keywords or subheadings to match."

        prompt = f"""
Analyze the semantic coherence between this main title (H1) and its subheadings (H2/H3).
The subheadings do NOT need to contain the exact words of the H1, but they must logically belong to the same topic or support it (e.g. if the H1 is about alternative destinations to Dubai, listing specific city/country names is perfectly coherent and should score 100%).

H1: "{h1}"
Subheadings:
{chr(10).join([f"- {s}" for s in subheadings_list])}

Respond in the following format:
SCORE: [0 to 100]
REASON: [Brief 1-sentence explanation of why the subheadings align or mismatch semantically with the H1]
"""
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        text = response.text or ""
        score = fallback_score
        reason = f"Completed semantic matching. (Overlap: {fallback_score:.1f}%)"
        for line in text.splitlines():
            if line.startswith("SCORE:"):
                try:
                    score = float(line.replace("SCORE:", "").strip())
                except:
                    pass
            elif line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()
        return score, reason
    except Exception as e:
        return fallback_score, f"Semantic matching fallback (API error: {e}): {fallback_score:.1f}% overlap."

def check_image_alt_coherence(h1: str, images: list) -> tuple[list, str]:
    """
    Checks if the image alt texts are semantically coherent with the H1/topic,
    or if they are keyword-stuffed / irrelevant.
    """
    # Filter out images that are missing alt tags
    images_with_alts = [img for img in images if img.get('alt', '').strip()]
    if not images_with_alts:
        return [], "No images with alt tags to check."

    # If testing or API keys are missing, skip semantic check
    is_testing = "PYTEST_CURRENT_TEST" in os.environ
    api_key = os.environ.get("GEMINI_API_KEY")
    if is_testing or not api_key:
        return [], "Skipped semantic alt check in test/offline mode."

    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        model_name = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash")

        image_data = [f"Image src: '{img.get('src')}', Alt: '{img.get('alt')}'" for img in images_with_alts]
        prompt = f"""
Analyze the semantic coherence of the following image alt texts against the main page topic (H1).
H1 Topic: "{h1}"

Images with Alt Texts:
{chr(10).join(image_data)}

Evaluate if any image alt texts are:
1. Semantically irrelevant to the main topic (H1).
2. Keyword-stuffed (contain unnatural lists of keywords instead of describing the image context).

Respond in the following format:
INCOHERENT_IMAGES: [List of image filenames/sources that are irrelevant or stuffed, comma-separated. Write 'None' if all are good]
REASON: [Brief explanation of why they are flagged]
"""
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        text = response.text or ""
        incoherent = []
        reason = "All alt texts are coherent."
        for line in text.splitlines():
            if line.startswith("INCOHERENT_IMAGES:"):
                val = line.replace("INCOHERENT_IMAGES:", "").strip()
                if val.lower() != "none" and val:
                    incoherent = [s.strip() for s in val.split(",") if s.strip()]
            elif line.startswith("REASON:"):
                reason = line.replace("REASON:", "").strip()
        return incoherent, reason
    except Exception as e:
        return [], f"Semantic alt check fallback (API error: {e})."

def run_audit(html_content: str, page_url: str = "") -> dict:
    """
    Runs all 19 technical SEO and AEO rules against the HTML content.
    Returns a dictionary of results grouped by severity:
      - 'errors': list of critical issues
      - 'warnings': list of warnings
      - 'passes': list of passed rules
      - 'metrics': dictionary of key page metrics
    """
    errors = []
    warnings = []
    passes = []
    metrics = {}

    if HAS_BS4:
        soup = BeautifulSoup(html_content, 'html.parser')
    else:
        # Simple fallback representation using regex for basic tag checks
        soup = None

    # Helper function to register findings
    def add_result(rule_name, condition, error_msg, success_msg, is_warning=False):
        if condition:
            if is_warning:
                warnings.append(f"**{rule_name}**: {error_msg}")
            else:
                errors.append(f"**{rule_name}**: {error_msg}")
        else:
            passes.append(f"**{rule_name}**: {success_msg}")

    # ==========================================
    # HEAD TAG RULES (1-5, 18, 19)
    # ==========================================

    # 1. Meta Title
    title_text = ""
    if soup:
        title_tag = soup.find('title')
        title_text = title_tag.get_text().strip() if title_tag else ""
    else:
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        title_text = title_match.group(1).strip() if title_match else ""

    metrics['title'] = title_text
    add_result(
        "Meta Title",
        not title_text or len(title_text) < 30 or len(title_text) > 60,
        f"Missing or sub-optimal title length ({len(title_text)} chars). Recommended: 30-60 chars. Value: '{title_text}'" if title_text else "Title tag is missing in <head>.",
        f"Passed title check ({len(title_text)} chars: '{title_text}')."
    )

    # 2. Meta Description
    desc_text = ""
    if soup:
        desc_tag = soup.find('meta', attrs={'name': re.compile(r'^description$', re.IGNORECASE)})
        desc_text = desc_tag.get('content', '').strip() if desc_tag else ""
    else:
        desc_match = re.search(r'<meta\s+[^>]*name=["\']description["\'][^>]*content=["\'](.*?)["\']', html_content, re.IGNORECASE)
        desc_text = desc_match.group(1).strip() if desc_match else ""

    metrics['description'] = desc_text
    add_result(
        "Meta Description",
        not desc_text or len(desc_text) < 70 or len(desc_text) > 160,
        f"Sub-optimal description length ({len(desc_text)} chars). Recommended: 70-160 chars. Value: '{desc_text}'" if desc_text else "Meta description is missing in <head>.",
        f"Passed description check ({len(desc_text)} chars)."
    )

    # 3. Open Graph Tags
    missing_og = []
    og_properties = ["title", "description", "image", "url"]
    for prop in og_properties:
        found = False
        if soup:
            found = bool(soup.find('meta', attrs={'property': f'og:{prop}'}))
        else:
            found = bool(re.search(rf'property=["\']og:{prop}["\']', html_content, re.IGNORECASE))
        if not found:
            missing_og.append(f"og:{prop}")

    add_result(
        "Open Graph Tags",
        len(missing_og) > 0,
        f"Missing key Open Graph tags: {', '.join(missing_og)}.",
        "All key Open Graph tags are configured correctly.",
        is_warning=True
    )

    # 4. Twitter Cards
    missing_twitter = []
    twitter_names = ["card", "title", "description", "image"]
    for name in twitter_names:
        found = False
        if soup:
            found = bool(soup.find('meta', attrs={'name': f'twitter:{name}'}))
        else:
            found = bool(re.search(rf'name=["\']twitter:{name}["\']', html_content, re.IGNORECASE))
        if not found:
            missing_twitter.append(f"twitter:{name}")

    add_result(
        "Twitter Cards",
        len(missing_twitter) > 0,
        f"Missing key Twitter Card tags: {', '.join(missing_twitter)}.",
        "All key Twitter Card tags are configured correctly.",
        is_warning=True
    )

    # 5. Canonical URL
    canonical_url = ""
    if soup:
        canonical_tag = soup.find('link', attrs={'rel': 'canonical'})
        canonical_url = canonical_tag.get('href', '').strip() if canonical_tag else ""
    else:
        canonical_match = re.search(r'<link\s+[^>]*rel=["\']canonical["\'][^>]*href=["\'](.*?)["\']', html_content, re.IGNORECASE)
        canonical_url = canonical_match.group(1).strip() if canonical_match else ""

    is_self_referential = True
    if page_url and canonical_url:
        page_path = urlparse(page_url).path.rstrip('/')
        canon_path = urlparse(canonical_url).path.rstrip('/')
        is_self_referential = (page_path == canon_path)

    add_result(
        "Canonical URL",
        not canonical_url or not is_self_referential,
        f"Canonical mismatch or missing. Page URL path: '{page_url}', Canonical path: '{canonical_url}'" if canonical_url else "Canonical link tag is missing.",
        f"Canonical URL configured correctly: '{canonical_url}'."
    )

    # 18. JSON-LD Schema
    schema_found = False
    if soup:
        schema_found = bool(soup.find('script', attrs={'type': 'application/ld+json'}))
    else:
        schema_found = bool(re.search(r'<script\s+[^>]*type=["\']application/ld\+json["\']', html_content, re.IGNORECASE))

    add_result(
        "JSON-LD Schema",
        not schema_found,
        "No structured JSON-LD schema found on this page.",
        "Structured JSON-LD schema block(s) detected.",
        is_warning=True
    )

    # 19. Robots Meta
    robots_content = ""
    if soup:
        robots_tag = soup.find('meta', attrs={'name': re.compile(r'^robots$', re.IGNORECASE)})
        robots_content = robots_tag.get('content', '').lower() if robots_tag else ""
    else:
        robots_match = re.search(r'<meta\s+[^>]*name=["\']robots["\'][^>]*content=["\'](.*?)["\']', html_content, re.IGNORECASE)
        robots_content = robots_match.group(1).lower() if robots_match else ""

    has_noindex = "noindex" in robots_content
    has_nofollow = "nofollow" in robots_content

    add_result(
        "Robots Meta",
        has_noindex or has_nofollow,
        f"Robots meta directive set to: '{robots_content}' (blocking search engines).",
        "Robots meta tag permits indexation (or is default-index).",
        is_warning=True
    )

    # ==========================================
    # HEADING & CONTENT RULES (6-11)
    # ==========================================

    headings = []
    if soup:
        for tag in soup.find_all(re.compile(r'^h[1-6]$', re.IGNORECASE)):
            headings.append((int(tag.name[1]), tag.get_text().strip()))
    else:
        heading_matches = re.findall(r'<h([1-6])[^>]*>(.*?)</h\1>', html_content, re.IGNORECASE | re.DOTALL)
        for lvl, text in heading_matches:
            # Clean HTML from headings if regex was used
            clean_text = re.sub(r'<[^>]+>', '', text).strip()
            headings.append((int(lvl), clean_text))

    # 6. H1 Count
    h1s = [txt for lvl, txt in headings if lvl == 1]
    add_result(
        "H1 Tag Count",
        len(h1s) != 1,
        f"Found {len(h1s)} H1 tags: {', '.join([f'\"{h}\"' for h in h1s])}. Exactly one H1 is required." if len(h1s) > 1 else "No H1 tag found on the page.",
        "Exactly one H1 tag exists."
    )

    # 7. Heading Hierarchy
    hierarchy_skipped = False
    skip_messages = []
    for i in range(len(headings) - 1):
        curr_lvl, curr_txt = headings[i]
        next_lvl, next_txt = headings[i+1]
        if next_lvl > curr_lvl + 1:
            hierarchy_skipped = True
            skip_messages.append(f"H{curr_lvl} ('{curr_txt[:30]}...') followed directly by H{next_lvl} ('{next_txt[:30]}...')")

    add_result(
        "Heading Hierarchy",
        hierarchy_skipped,
        f"Hierarchical heading level skips detected: {'; '.join(skip_messages)}.",
        "Heading levels nest sequentially without skips.",
        is_warning=True
    )

    # 8. Empty Headings
    empty_headings_count = sum(1 for lvl, txt in headings if not txt)
    add_result(
        "Empty Headings",
        empty_headings_count > 0,
        f"Found {empty_headings_count} empty heading tags (missing text).",
        "No empty heading elements detected.",
        is_warning=True
    )

    # Body plain text extraction
    if soup:
        body_tag = soup.find('body')
        body_text = body_tag.get_text() if body_tag else soup.get_text()
    else:
        # Strip script/style tags first
        clean_html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        body_text = re.sub(r'<[^>]+>', ' ', clean_html)

    words = [w for w in body_text.split() if w]
    word_count = len(words)
    metrics['word_count'] = word_count

    # 9. Thin Content
    add_result(
        "Thin Content Check",
        word_count < 300,
        f"Thin content detected: {word_count} words. Google prefers substantial articles (>= 300 words).",
        f"Page content length is acceptable ({word_count} words)."
    )

    # 10. Readability (Average Sentence Length)
    # Split text into sentences using simple punctuation check
    sentences = [s.strip() for s in re.split(r'[.!?]+', body_text) if s.strip()]
    sentence_count = len(sentences)
    avg_sentence_len = (word_count / sentence_count) if sentence_count > 0 else 0
    metrics['avg_sentence_len'] = avg_sentence_len

    add_result(
        "Readability Metric",
        avg_sentence_len > 25,
        f"Sentence structure is dense. Average sentence length is {avg_sentence_len:.1f} words (recommended < 25).",
        f"Excellent sentence readability (Average length: {avg_sentence_len:.1f} words).",
        is_warning=True
    )

    # 11. Title-Content Semantic Matching
    h1_val = title_text or (h1s[0] if h1s else "")
    match_score, match_reason = check_semantic_alignment(h1_val, headings)

    metrics['semantic_match_score'] = match_score
    add_result(
        "Topical Alignment",
        match_score < 40.0,
        f"Low topical coherence ({match_score:.1f}% alignment). {match_reason}",
        f"Passed semantic matching check ({match_score:.1f}% alignment). {match_reason}",
        is_warning=True
    )

    # ==========================================
    # IMAGE RULES (12-14)
    # ==========================================

    images = []
    if soup:
        for img in soup.find_all('img'):
            images.append(img.attrs)
    else:
        # Regex to parse image attrs
        img_tags = re.findall(r'<img\s+([^>]*?)>', html_content, re.IGNORECASE)
        for attrs_str in img_tags:
            attrs = {}
            for match in re.finditer(r'(\w+)=["\'](.*?)["\']', attrs_str):
                attrs[match.group(1).lower()] = match.group(2)
            images.append(attrs)

    metrics['images_count'] = len(images)

    # 12. Image Alt Text Accessibility
    missing_alt_images = []
    generic_alt_images = []
    generic_words = {"image", "screenshot", "pic", "logo", "icon", "placeholder", "img", "photo", "banner"}

    for img in images:
        src = img.get('src', 'unknown')
        alt = img.get('alt', '').strip()
        if not alt:
            missing_alt_images.append(src)
        else:
            alt_lower = alt.lower()
            if alt_lower in generic_words or len(alt_lower) < 4:
                generic_alt_images.append((src, alt))
            elif any(ext in alt_lower for ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]):
                generic_alt_images.append((src, alt))

    # Live Semantic Alt Coherence Check
    incoherent_alt_images, semantic_reason = check_image_alt_coherence(
        title_text or (h1s[0] if h1s else ""),
        images
    )

    has_alt_issue = len(missing_alt_images) > 0 or len(generic_alt_images) > 0 or len(incoherent_alt_images) > 0
    error_parts = []
    if missing_alt_images:
        error_parts.append(f"Found {len(missing_alt_images)} image(s) missing alt tags (e.g. '{os.path.basename(missing_alt_images[0])}')")
    if generic_alt_images:
        error_parts.append(f"Found {len(generic_alt_images)} image(s) with generic/non-descriptive alt text (e.g. '{generic_alt_images[0][1]}')")
    if incoherent_alt_images:
        error_parts.append(f"Found {len(incoherent_alt_images)} image(s) with semantically incoherent or stuffed alt text (e.g. '{os.path.basename(incoherent_alt_images[0])}')")

    add_result(
        "Image Alt Text",
        has_alt_issue,
        f"{' and '.join(error_parts)}. {semantic_reason} Accessible alt text should describe the image context and relate to the page topic.",
        f"All images have descriptive, accessible alt tags configured. {semantic_reason}",
        is_warning=True
    )

    # 13. Image Dimensions
    missing_dims_images = [img.get('src', 'unknown') for img in images if not img.get('width') or not img.get('height')]
    add_result(
        "Image Dimensions",
        len(missing_dims_images) > 0,
        f"Found {len(missing_dims_images)} image(s) missing width and/or height attributes. Examples: {', '.join([os.path.basename(s) for s in missing_dims_images[:3]])}.",
        "All images have layout dimension attributes.",
        is_warning=True
    )

    # 14. First Image Lazy Loading
    first_img_lazy = False
    if images:
        first_img = images[0]
        # Check if first image is lazy-loaded
        if "lazy" in first_img.get("loading", "").lower():
            first_img_lazy = True

    add_result(
        "First Image Lazyload",
        first_img_lazy,
        "First body image has loading='lazy' (demotes Largest Contentful Paint). Change to eager.",
        "First image loaded eagerly (improves LCP score).",
        is_warning=True
    )

    # ==========================================
    # LINK RULES (15-17)
    # ==========================================

    links = []
    if soup:
        for a in soup.find_all('a'):
            links.append((a.get('href', ''), a.get_text().strip()))
    else:
        # Regex to match anchor href and text
        a_matches = re.findall(r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>', html_content, re.IGNORECASE | re.DOTALL)
        for href, txt in a_matches:
            clean_txt = re.sub(r'<[^>]+>', '', txt).strip()
            links.append((href, clean_txt))

    # 15. Generic Anchor Copy
    generic_patterns = {r'\bclick\s+here\b', r'\bread\s+more\b', r'\blearn\s+more\b', r'\bgo\s+here\b'}
    generic_links = []
    for href, txt in links:
        for pattern in generic_patterns:
            if re.search(pattern, txt, re.IGNORECASE):
                generic_links.append((href, txt))
                break

    add_result(
        "Generic Anchor Text",
        len(generic_links) > 0,
        f"Found {len(generic_links)} generic anchor link(s) (e.g. '{generic_links[0][1]}' linking to '{generic_links[0][0]}')." if generic_links else "",
        "No generic link anchors found on page.",
        is_warning=True
    )

    # 16. Mixed Content
    mixed_content = []
    # Check all src and href attributes in the document (only if parent page is HTTPS)
    if page_url.startswith("https://"):
        if soup:
            for tag in soup.find_all(src=True):
                src = tag.get('src')
                if src.startswith('http://'):
                    mixed_content.append(src)
            for tag in soup.find_all('link', href=True):
                href = tag.get('href')
                if href.startswith('http://'):
                    mixed_content.append(href)
        else:
            matches = re.findall(r'(src|href)=["\'](http://.*?)["\']', html_content, re.IGNORECASE)
            mixed_content = [m[1] for m in matches]

    add_result(
        "Mixed Content Check",
        len(mixed_content) > 0,
        f"Found {len(mixed_content)} insecure HTTP asset(s) loaded (mixed content): {', '.join(mixed_content[:3])}.",
        "No insecure HTTP resources found (mixed content check passed)." if page_url.startswith("https://") else "Mixed content check skipped (page is served over HTTP)."
    )

    # 17. Outgoing Links (Orphan check)
    add_result(
        "Orphan Page Check",
        len(links) == 0,
        "No hyperlinks found in page body. Add internal/external links to ensure crawler flow.",
        f"Found {len(links)} outgoing link(s)."
    )

    return {
        "errors": errors,
        "warnings": warnings,
        "passes": passes,
        "metrics": metrics
    }

def generate_report_html(results: dict, wp_post_id: str, page_url: str) -> str:
    """
    Renders the structured audit results dictionary into a premium dark-themed HTML report
    using the template file at app/templates/audit_template.html.
    """
    import datetime
    from jinja2 import Template

    # Path to template
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "audit_template.html"
    )

    # Load template content
    if os.path.exists(template_path):
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                template_content = f.read()
        except Exception:
            template_content = "<html><body><h1>Audit Report (Load Failed)</h1></body></html>"
    else:
        template_content = "<html><body><h1>Audit Report (Template Missing)</h1></body></html>"

    # Render with Jinja2
    try:
        template = Template(template_content)
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Clean markdown bolding into HTML strong tags
        def clean_markdown_bold(items):
            return [re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', item) for item in items]

        return template.render(
            wp_post_id=wp_post_id,
            page_url=page_url,
            timestamp=now_str,
            metrics=results["metrics"],
            errors=clean_markdown_bold(results["errors"]),
            warnings=clean_markdown_bold(results["warnings"]),
            passes=clean_markdown_bold(results["passes"])
        )
    except Exception as e:
        return f"<html><body><h1>Audit Report (Render Error)</h1><p>{e}</p></body></html>"
