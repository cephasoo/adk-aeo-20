---
name: serp-feature-and-intent-auditor
description: Classifies search queries into Navigational, Informational, Commercial, or Transactional intent using Gemini, audits target URL rankings inside organic and paid listings, and performs inclusion/exclusion audits and content scaling recommendations.
---

# serp-feature-and-intent-auditor Instructions

When the user requests to track a keyword or audit ranking visibility, the agent must leverage the `serp_position_tracker` tool to retrieve the search intent classification, organic/paid rankings, and SERP features.

## Semantic Matching & Alignment Scoring (Inclusion)
Evaluate the audited target page's HTML structure for intent alignment:
- **Informational Intent**: Verify the page has structured headings (H2/H3), explanatory paragraphs, and no intrusive sales forms.
- **Transactional Intent**: Verify the page contains action elements, buttons, prices, or checkout routes.
- **Commercial Intent**: Verify the page contains review highlights, comparison charts, or feature listings.
- **Navigational Intent**: Verify the page is a direct brand destination.

Compute an **Intent Alignment Score** (0-100%) and include it in the report, detailing any mismatch.

## Exclusion Auditing & Content Gap Analysis (Exclusion)
If the target URL is not ranking in the top organic results:
1. **Analyze Competitor Cues**: Inspect the titles, snippets, and domains of the top 3 ranking search results in the `serp_position_tracker` output.
2. **Determine Dominant Format**: Classify the format of these ranking sites (e.g., are they informational comparisons, product categories, or how-to guides?).
3. **Diagnose Mismatch**: If the target page is a product page but the top results are informational comparison articles, flag an **Intent Mismatch** as the primary reason for exclusion.
4. **Formulate Content Scaling Roadmap**: Recommend concrete action items:
   - Suggest creating a new article/page matching the dominant intent (with title and structure ideas).
   - Advise on incorporating specific sub-questions extracted from the People Also Ask (PAA) list.
   - Detail how to link the new informational asset back to the target transactional page to recover ROI.
