# SEO & AEO Rulebook

This reference documents the 19 technical checks performed by the Advanced SEO Auditor.

## Meta Head Tags (Social & Search Coverage)

### Rule 1: Meta Title
- **Requirement**: Must have `<title>` in `<head>`. Recommended length: 30 to 60 characters.
- **Why**: Google truncates titles longer than 60 chars. Too short titles fail to establish relevance.

### Rule 2: Meta Description
- **Requirement**: Must have `<meta name="description">` in `<head>`. Recommended length: 70 to 160 characters.
- **Why**: Used for search result snippets. Too short or missing descriptions limit click-through rates.

### Rule 3: Open Graph Tags
- **Requirement**: Requires `og:title`, `og:description`, `og:image`, and `og:url`.
- **Why**: Ensures rich visual preview when links are shared on social media and chat apps (Slack, Twitter, WhatsApp).

### Rule 4: Twitter Cards
- **Requirement**: Requires `twitter:card`, `twitter:title`, `twitter:description`, and `twitter:image`.
- **Why**: Standard social markup specifically targeting Twitter/X indexers and cards.

### Rule 5: Canonical Link
- **Requirement**: `<link rel="canonical" href="...">` must be present and match the page URL (self-referential).
- **Why**: Prevents duplicate content issues and consolidates link equity.

---

## Layout & Semantic Structure

### Rule 6: Primary H1 Count
- **Requirement**: Exactly one `<h1>` tag must exist.
- **Why**: Serves as the primary content header. Multiple H1 tags confuse crawler contextual mapping.

### Rule 7: Heading Hierarchy Sequentiality
- **Requirement**: Heading levels must not skip levels (e.g. H2 followed by H4 without H3).
- **Why**: Helps assistive technologies and crawlers navigate structural hierarchy.

### Rule 8: Empty Headings
- **Requirement**: No headings should contain only whitespace or be empty (e.g., `<h3></h3>`).
- **Why**: Common artifact of visual editors that leaves empty DOM elements, confusing screen readers.

---

## Content Depth & Readability

### Rule 9: Thin Content Check
- **Requirement**: Content must have at least 300 words.
- **Why**: Search engines downrank shallow pages that lack useful context or substantial information.

### Rule 10: Readability (Sentence Length)
- **Requirement**: Sentences should average under 25 words.
- **Why**: Short, clear sentences are favored by modern search and answer engine LLM summarization systems.

### Rule 11: Title-Content Semantic Matching
- **Requirement**: Check that subheadings share a thematic/keyword overlap of at least 40% with the primary H1 title.
- **Why**: Detects topical drift where sections of a page drift off-topic, diluting semantic relevance.

---

## Image Optimization

### Rule 12: Alt Text
- **Requirement**: Every image must have an `alt="..."` attribute.
- **Why**: Critical for accessibility and image search indexing.

### Rule 13: Dimension Attributes
- **Requirement**: Images should have explicit `width` and `height` attributes.
- **Why**: Prevents layout shifts during rendering (Cumulative Layout Shift / Core Web Vitals).

### Rule 14: Above-the-Fold Lazy Loading
- **Requirement**: The first image on the page must NOT have `loading="lazy"`.
- **Why**: Above-the-fold images should load eagerly to improve Largest Contentful Paint (LCP) performance.

---

## Link Health & Page Flow

### Rule 15: Generic Anchor Copy
- **Requirement**: Avoid links with text like "Click here", "Read more", or "Learn more".
- **Why**: Descriptive anchor text gives context to crawlers about the destination page.

### Rule 16: Mixed Content Check
- **Requirement**: No resources (`src`, `href`) should use insecure `http://` on an `https://` site.
- **Why**: Google demotes pages loading mixed/insecure assets.

### Rule 17: Outgoing Links (Orphan check)
- **Requirement**: Body should have at least one internal/external link.
- **Why**: Prevents dead-end user experiences.

---

## Schema & Directives

### Rule 18: JSON-LD Schema
- **Requirement**: Detect at least one `<script type="application/ld+json">`.
- **Why**: Standard vehicle for structured metadata.

### Rule 19: Robots Meta
- **Requirement**: Detect if any meta tags have `noindex` or `nofollow` directives.
- **Why**: Helps confirm the page isn't blocked from indexation by accident.
