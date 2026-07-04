# Technical SEO & AEO Auditor Skill

This skill extends Antigravity agents with production-grade search optimization auditing capabilities. It parses rendered HTML, checks meta tags, runs semantic analysis, tracks rankings, and integrates Google Search Console and SerpAPI.

## Skill Structure
- **Instructions**: [SKILL.md](file:///C:/Users/USER/secure-agent-lab/gutenberg-aeo-copilot/.agents/skills/seo-auditor/SKILL.md)
- **Rules & Reference**: [seo_rulebook.md](file:///C:/Users/USER/secure-agent-lab/gutenberg-aeo-copilot/.agents/skills/seo-auditor/references/seo_rulebook.md)
- **HTML Layout Template**: [audit_template.html](file:///C:/Users/USER/secure-agent-lab/gutenberg-aeo-copilot/app/templates/audit_template.html)
- **Audit Rules Engine**: [audit_rules.py](file:///C:/Users/USER/secure-agent-lab/gutenberg-aeo-copilot/app/tools/audit_rules.py)
- **API & Diagnostic Toolset**: [seo_tools.py](file:///C:/Users/USER/secure-agent-lab/gutenberg-aeo-copilot/app/tools/seo_tools.py)

## Tool Definitions

### `advanced_seo_audit(wp_post_id_or_url: str) -> str`
Fetches a WordPress page's rendered frontend HTML and audits it against 19 core SEO rules. Writes full reports to `wp-content/uploads/aeo-audits/` and returns a Telegram summary.

### `serp_position_tracker(target_url: str, search_query: str) -> str`
Uses SerpAPI to track the ranking position of `target_url` for `search_query`.

### `aeo_citation_checker(search_query: str, target_url: str) -> str`
Uses SerpAPI's AI Mode/AI Overview to check if `target_url` is cited in generative answers.

### `gsc_indexing_inspector(page_url: str) -> str`
Gated GSC inspector to check indexing status and rich results eligibility.

### `gsc_performance_report(days: int = 28) -> str`
GSC performance dashboard overview for clicks, impressions, and CTR.

### `gsc_page_query_analysis(page_url: str) -> str`
Lists all queries driving traffic to a specific page.

### `canonical_audit(urls: str) -> str`
Audits multiple URLs for canonical tags and cannibalization.

### `redirect_chain_detector(url: str) -> str`
Traces redirect loops and chains.
