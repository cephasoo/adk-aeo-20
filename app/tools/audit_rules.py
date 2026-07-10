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
        from app.config import DEFAULT_GEMINI_MODEL
        model_name = DEFAULT_GEMINI_MODEL

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
        from app.config import DEFAULT_GEMINI_MODEL
        model_name = DEFAULT_GEMINI_MODEL

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

def run_audit(html_content: str, page_url: str = "", intent: str = "") -> dict:
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
    # Strip script/style/noscript tags to prevent JSON-LD and JS from
    # polluting word counts and sentence length calculations.
    if soup:
        import copy
        temp_soup = copy.copy(soup)
        for noise_tag in temp_soup.find_all(['script', 'style', 'noscript']):
            noise_tag.decompose()
        body_tag = temp_soup.find('body')
        # Use separator='\n' so each block element becomes its own line,
        # preventing headings/list items from merging into one run-on sentence.
        body_text = body_tag.get_text(separator='\n') if body_tag else temp_soup.get_text(separator='\n')
    else:
        # Strip script/style tags first
        clean_html = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', '', html_content, flags=re.IGNORECASE | re.DOTALL)
        body_text = re.sub(r'<[^>]+>', '\n', clean_html)

    # Collapse whitespace within lines but preserve line breaks
    body_text = re.sub(r'[^\S\n]+', ' ', body_text)
    body_text = re.sub(r'\n\s*\n', '\n', body_text).strip()

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
    # Split on punctuation terminators AND newlines, since bullet-list pages
    # use line breaks rather than periods to delimit distinct statements.
    raw_segments = re.split(r'[.!?]+|\n', body_text)
    sentences = [s.strip() for s in raw_segments if len(s.strip().split()) >= 3]
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
    # IMAGE OPTIMIZATION RULES (20-26)
    # ==========================================

    # 20. Next-Gen Image Format Detection
    modern_formats = {'webp', 'avif', 'svg'}
    legacy_formats = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff'}
    legacy_image_count = 0
    modern_image_count = 0
    legacy_only_images = []  # images with legacy format AND no <picture> fallback

    for img in images:
        src = img.get('src', '')
        if not src:
            continue
        # Strip query params and fragments to get clean filename
        clean_src = src.split('?')[0].split('#')[0]
        ext = os.path.splitext(clean_src)[1].lstrip('.').lower()
        if ext in modern_formats:
            modern_image_count += 1
        elif ext in legacy_formats:
            # Check if this image is inside a <picture> element with modern sources (BS4 only)
            has_picture_fallback = False
            if soup:
                # Find the actual img tag in the soup by src
                img_tag = soup.find('img', attrs={'src': src})
                if img_tag:
                    picture_parent = img_tag.find_parent('picture')
                    if picture_parent:
                        sources = picture_parent.find_all('source')
                        for source in sources:
                            source_type = source.get('type', '').lower()
                            source_srcset = source.get('srcset', '').lower()
                            if any(fmt in source_type or fmt in source_srcset for fmt in modern_formats):
                                has_picture_fallback = True
                                break
            if has_picture_fallback:
                modern_image_count += 1  # Has modern fallback via <picture>
            else:
                legacy_image_count += 1
                legacy_only_images.append(os.path.basename(clean_src))

    metrics['legacy_image_count'] = legacy_image_count
    metrics['modern_image_count'] = modern_image_count
    total_format_images = legacy_image_count + modern_image_count

    legacy_ratio = (legacy_image_count / total_format_images) if total_format_images > 0 else 0
    add_result(
        "Image Format",
        legacy_ratio > 0.5,
        f"{legacy_image_count} of {total_format_images} images use legacy-only formats (no <picture> fallback). "
        f"Examples: {', '.join(legacy_only_images[:3])}. Consider converting to WebP/AVIF.",
        f"Good image format usage: {modern_image_count} modern vs {legacy_image_count} legacy format(s).",
        is_warning=True
    )

    # 21. Responsive Image Audit (srcset/sizes)
    responsive_image_count = 0
    missing_responsive = []
    content_images_for_responsive = []

    for img in images:
        src = img.get('src', '')
        # Exclude small images (icons/logos)
        src_lower = src.lower()
        if 'icon' in src_lower or 'logo' in src_lower:
            continue
        # Exclude by explicit dimensions <= 100px
        try:
            w = int(img.get('width', 0))
            h = int(img.get('height', 0))
            if 0 < w <= 100 or 0 < h <= 100:
                continue
        except (ValueError, TypeError):
            pass
        content_images_for_responsive.append(img)

        if img.get('srcset'):
            responsive_image_count += 1
            # Check if sizes attribute is also present
            if not img.get('sizes'):
                missing_responsive.append(os.path.basename(src.split('?')[0]))
        else:
            missing_responsive.append(os.path.basename(src.split('?')[0]))

    metrics['responsive_image_count'] = responsive_image_count
    total_content_responsive = len(content_images_for_responsive)
    non_responsive_ratio = (len(missing_responsive) / total_content_responsive) if total_content_responsive > 0 else 0

    add_result(
        "Responsive Images",
        non_responsive_ratio > 0.5,
        f"{len(missing_responsive)} of {total_content_responsive} content images lack srcset/sizes responsive variants. "
        f"Examples: {', '.join(missing_responsive[:3])}.",
        f"{responsive_image_count} of {total_content_responsive} content images have responsive srcset attributes.",
        is_warning=True
    )

    # 22. LCP Image fetchpriority
    lcp_has_priority = False
    lcp_message = ""
    if images:
        first_img = images[0]
        has_fetchpriority = first_img.get('fetchpriority', '').lower() == 'high'
        has_eager_loading = first_img.get('loading', '').lower() == 'eager'
        lcp_has_priority = has_fetchpriority or has_eager_loading
        if has_fetchpriority:
            lcp_message = "First image has fetchpriority='high' for optimal LCP."
        elif has_eager_loading:
            lcp_message = "First image has loading='eager' (consider also adding fetchpriority='high')."
    else:
        lcp_has_priority = True  # No images, no issue
        lcp_message = "No images found to check."

    add_result(
        "LCP Image Priority",
        not lcp_has_priority,
        "First body image is missing fetchpriority='high' and loading='eager'. "
        "Add fetchpriority='high' to the LCP candidate image for faster rendering.",
        lcp_message,
        is_warning=True
    )

    # 23. Image Filename Semantics
    non_descriptive_filenames = []
    descriptive_count = 0
    # Patterns for non-descriptive filenames
    hash_pattern = re.compile(r'[0-9a-f]{8,}', re.IGNORECASE)
    sequential_pattern = re.compile(r'^(IMG_|DSC_|Screenshot_|image)\d+', re.IGNORECASE)
    uuid_pattern = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
    numeric_pattern = re.compile(r'^\d+$')
    single_char_pattern = re.compile(r'^[a-zA-Z0-9]$')

    for img in images:
        src = img.get('src', '')
        if not src:
            continue
        # Extract filename, strip query params
        clean_src = src.split('?')[0].split('#')[0]
        filename = os.path.basename(clean_src)
        name_without_ext = os.path.splitext(filename)[0]

        if not name_without_ext:
            continue

        is_non_descriptive = False
        # Check single character or purely numeric
        if single_char_pattern.match(name_without_ext) or numeric_pattern.match(name_without_ext):
            is_non_descriptive = True
        # Check UUID-like
        elif uuid_pattern.search(name_without_ext):
            is_non_descriptive = True
        # Check sequential naming patterns
        elif sequential_pattern.match(name_without_ext):
            is_non_descriptive = True
        # Check hash-like (8+ consecutive hex chars making up most of the name)
        elif hash_pattern.match(name_without_ext) and len(name_without_ext) >= 8:
            is_non_descriptive = True

        if is_non_descriptive:
            non_descriptive_filenames.append(filename)
        else:
            descriptive_count += 1

    metrics['descriptive_filenames'] = descriptive_count

    add_result(
        "Image Filename Semantics",
        len(non_descriptive_filenames) > 0,
        f"Found {len(non_descriptive_filenames)} non-descriptive image filename(s): "
        f"{', '.join(non_descriptive_filenames[:5])}. Use descriptive, keyword-rich filenames.",
        "All image filenames are descriptive and SEO-friendly.",
        is_warning=True
    )

    # 24. Figure + Figcaption Semantic Wrapping (BS4 path only)
    if soup:
        figure_wrapped_count = 0
        figure_eligible_images = 0

        for img_tag in soup.find_all('img'):
            src = img_tag.get('src', '').lower()
            # Exclude small/icon images
            if 'icon' in src or 'logo' in src:
                continue
            try:
                w = int(img_tag.get('width', 0))
                h = int(img_tag.get('height', 0))
                if 0 < w < 100 or 0 < h < 100:
                    continue
            except (ValueError, TypeError):
                pass

            figure_eligible_images += 1

            # Check if parent or grandparent is <figure>
            parent = img_tag.parent
            grandparent = parent.parent if parent else None
            figure_el = None
            if parent and parent.name == 'figure':
                figure_el = parent
            elif grandparent and grandparent.name == 'figure':
                figure_el = grandparent

            if figure_el:
                # Check for <figcaption> sibling within the figure
                if figure_el.find('figcaption'):
                    figure_wrapped_count += 1

        figure_ratio = (figure_wrapped_count / figure_eligible_images) if figure_eligible_images > 0 else 1.0
        add_result(
            "Figure Semantic Wrapping",
            figure_ratio < 0.5,
            f"Only {figure_wrapped_count} of {figure_eligible_images} content images are wrapped in "
            f"<figure> with <figcaption>. Semantic wrapping improves accessibility and SEO context.",
            f"{figure_wrapped_count} of {figure_eligible_images} content images have proper <figure>/<figcaption> wrapping.",
            is_warning=True
        )
    else:
        # Regex fallback: skip this rule, as detecting parent elements is unreliable
        passes.append("**Figure Semantic Wrapping**: Skipped (requires HTML parser for DOM traversal).")

    # 25. Decorative Image Classification + SVG Accessibility
    decorative_patterns = ['icon', 'spacer', 'divider', 'bullet', 'arrow', 'chevron']
    over_described_decorative = []

    for img in images:
        src = img.get('src', '').lower()
        alt = img.get('alt', '').strip()

        # Determine if image is likely decorative
        is_decorative = False
        if any(pattern in src for pattern in decorative_patterns):
            is_decorative = True
        else:
            try:
                w = int(img.get('width', 0))
                h = int(img.get('height', 0))
                if 0 < w <= 48 and 0 < h <= 48:
                    is_decorative = True
            except (ValueError, TypeError):
                pass

        # If decorative AND alt text has > 3 words, flag as over-described
        if is_decorative and alt and len(alt.split()) > 3:
            over_described_decorative.append(os.path.basename(img.get('src', '')))

    # Part B: SVG Accessibility (BS4 only)
    inaccessible_svgs = 0
    total_svgs = 0
    if soup:
        body_tag_svg = soup.find('body')
        svg_container = body_tag_svg if body_tag_svg else soup
        for svg_tag in svg_container.find_all('svg'):
            total_svgs += 1
            has_role = svg_tag.get('role', '').lower() == 'img'
            has_aria_label = bool(svg_tag.get('aria-label'))
            has_aria_labelledby = bool(svg_tag.get('aria-labelledby'))
            if not (has_role and (has_aria_label or has_aria_labelledby)):
                inaccessible_svgs += 1

    has_decorative_issue = len(over_described_decorative) > 0 or inaccessible_svgs > 0
    error_parts_decorative = []
    if over_described_decorative:
        error_parts_decorative.append(
            f"{len(over_described_decorative)} decorative image(s) have verbose alt text (>3 words): "
            f"{', '.join(over_described_decorative[:3])}. Use alt='' for decorative images."
        )
    if inaccessible_svgs > 0:
        error_parts_decorative.append(
            f"{inaccessible_svgs} of {total_svgs} inline SVG(s) missing role='img' + aria-label/aria-labelledby."
        )

    add_result(
        "Decorative Image Classification",
        has_decorative_issue,
        " ".join(error_parts_decorative),
        f"Decorative images properly classified. "
        f"{total_svgs} inline SVG(s) have correct accessibility attributes." if total_svgs > 0
        else "Decorative images properly classified. No inline SVGs found.",
        is_warning=True
    )

    # 26. OG/Twitter Image Dimension Hints
    og_width = ""
    og_height = ""
    twitter_card_type = ""

    if soup:
        og_w_tag = soup.find('meta', attrs={'property': 'og:image:width'})
        og_h_tag = soup.find('meta', attrs={'property': 'og:image:height'})
        og_width = og_w_tag.get('content', '').strip() if og_w_tag else ""
        og_height = og_h_tag.get('content', '').strip() if og_h_tag else ""
        tc_tag = soup.find('meta', attrs={'name': 'twitter:card'})
        twitter_card_type = tc_tag.get('content', '').strip().lower() if tc_tag else ""
    else:
        og_w_match = re.search(r'property=["\']og:image:width["\'][^>]*content=["\'](\d+)["\']', html_content, re.IGNORECASE)
        og_h_match = re.search(r'property=["\']og:image:height["\'][^>]*content=["\'](\d+)["\']', html_content, re.IGNORECASE)
        og_width = og_w_match.group(1) if og_w_match else ""
        og_height = og_h_match.group(1) if og_h_match else ""
        tc_match = re.search(r'name=["\']twitter:card["\'][^>]*content=["\']([^"\']+)["\']', html_content, re.IGNORECASE)
        twitter_card_type = tc_match.group(1).strip().lower() if tc_match else ""

    social_dim_issues = []

    if not og_width or not og_height:
        social_dim_issues.append("og:image:width and/or og:image:height meta tags are missing.")
    else:
        try:
            w = int(og_width)
            h = int(og_height)
            if w < 200 or h < 200:
                social_dim_issues.append(
                    f"OG image dimensions ({w}x{h}) are below minimum 200x200. "
                    f"Recommended: 1200x630."
                )
        except (ValueError, TypeError):
            social_dim_issues.append(f"OG image dimensions are not valid integers: '{og_width}x{og_height}'.")

    if twitter_card_type == 'summary_large_image' and og_width and og_height:
        try:
            w = int(og_width)
            h = int(og_height)
            if w < 300 or h < 157:
                social_dim_issues.append(
                    f"Twitter summary_large_image requires minimum 300x157, found {w}x{h}."
                )
        except (ValueError, TypeError):
            pass

    add_result(
        "Social Image Dimensions",
        len(social_dim_issues) > 0,
        " ".join(social_dim_issues),
        f"OG image dimensions specified ({og_width}x{og_height}) and meet platform minimums.",
        is_warning=True
    )

    # 27. Dynamic Schema Type Awareness (Frontier Enhancement)
    SCHEMA_REGISTRY = {
        "informational": {
            "eligible": ["Article", "Course", "HowTo", "QAPage", "Dataset"],
            "deprecated_rich_results": ["FAQPage"],  # May 2026 deprecation
        },
        "commercial": {
            "eligible": ["Product", "SoftwareApplication", "Offer", "Review", "AggregateRating"],
        },
        "organization": {
            "eligible": ["Organization", "LocalBusiness", "Person", "WebSite", "ProfilePage"],
        },
        "media": {
            "eligible": ["VideoObject", "Podcast", "Book", "Recipe", "Event"],
        },
        "compliance": {
            "eligible": ["MedicalWebPage", "HealthTopicContent"],  # YMYL-specific
        },
    }

    import json
    schema_types_present = set()

    if soup:
        script_tags = soup.find_all('script', attrs={'type': 'application/ld+json'})
        for tag in script_tags:
            try:
                data = json.loads(tag.get_text() or '')
                def extract_types(obj):
                    if isinstance(obj, dict):
                        if "@type" in obj:
                            t = obj["@type"]
                            if isinstance(t, list):
                                for item in t:
                                    if isinstance(item, str):
                                        schema_types_present.add(item)
                            elif isinstance(t, str):
                                schema_types_present.add(t)
                        for v in obj.values():
                            extract_types(v)
                    elif isinstance(obj, list):
                        for item in obj:
                            extract_types(item)
                extract_types(data)
            except Exception:
                pass
    else:
        # Regex fallback
        matches = re.findall(r'["\']@type["\']\s*:\s*["\']([^"\']+)["\']', html_content)
        for m in matches:
            schema_types_present.add(m)

    schema_types_present = list(schema_types_present)
    metrics['schema_types_present'] = schema_types_present

    # Determine missing relevant types based on intent
    missing_relevant = []
    deprecated_present = []

    intent_clean = (intent or "").lower().strip()
    mapped_registry_keys = []
    if "informational" in intent_clean:
        mapped_registry_keys.append("informational")
    if "commercial" in intent_clean or "transactional" in intent_clean:
        mapped_registry_keys.append("commercial")

    # Always check organization
    mapped_registry_keys.append("organization")

    for r_key in mapped_registry_keys:
        reg = SCHEMA_REGISTRY.get(r_key, {})
        for el in reg.get("eligible", []):
            if el not in schema_types_present:
                missing_relevant.append(el)
        for dep in reg.get("deprecated_rich_results", []):
            if dep in schema_types_present:
                deprecated_present.append(dep)

    # Check deprecated schemas from other sections
    for r_key, reg in SCHEMA_REGISTRY.items():
        if r_key not in mapped_registry_keys:
            for dep in reg.get("deprecated_rich_results", []):
                if dep in schema_types_present:
                    deprecated_present.append(dep)

    # De-duplicate lists
    missing_relevant = sorted(list(set(missing_relevant)))
    deprecated_present = sorted(list(set(deprecated_present)))

    metrics['schema_types_missing'] = missing_relevant
    metrics['schema_types_deprecated'] = deprecated_present

    schema_warning_messages = []
    if deprecated_present:
        schema_warning_messages.append(
            f"Deprecated schema types found: {', '.join(deprecated_present)}. "
            "FAQPage schema is no longer supported by Google for rich results (deprecated May 2026), but is harmless to keep."
        )
    if missing_relevant:
        schema_warning_messages.append(
            f"Missing eligible schema types for intent '{intent_clean or 'unclassified'}': {', '.join(missing_relevant)}. "
            "Consider adding these schemas to improve semantic search visibility."
        )

    has_schema_issue = len(schema_warning_messages) > 0

    add_result(
        "Schema Type Awareness",
        has_schema_issue,
        " ".join(schema_warning_messages),
        f"Structured schema types parsed successfully: {', '.join(schema_types_present)}. "
        "No deprecated or missing relevant schemas flagged.",
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
