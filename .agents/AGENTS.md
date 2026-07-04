# Project Rules

- **Gemini Model Choice**: Always configure and use the `gemini-2.5-flash` model for agent runtime and testing. This model has high capacity, stable performance, and handles long contexts and multiple parallel tool calls without hitting the daily rate limits or 503 errors present on older or preview models (like `gemini-2.5-flash-lite` or `gemini-3.5-flash`).

- **Structured Data & FAQ Schema Constraints**:
  - NEVER recommend or generate FAQ structured data (`FAQPage` schema) for standard commercial, transactional, e-commerce, or generic niche/travel blog websites.
  - Understand that Google's August 2023 Core Update deprecated FAQ rich results for most sites. FAQ schema is strictly restricted to high-authority, official domains (e.g., government, medical, institutional portals).
  - Instead, recommend and generate standard structured data types aligned with intent (e.g., `Article`, `Product`, `LocalBusiness`, `Organization`, `Recipe`, `Review`) by referencing Google's official Search Gallery: `https://developers.google.com/search/docs/appearance/structured-data/search-gallery`.
  - Authoritative reference tool: When verifying structured data rules, use the `google-developer-knowledge` MCP server tools (like `answer_query` or `search_documents`) to pull the latest rules directly from Google's official developer docs.
