# Project Rules

- **Gemini Model Choice**: Always configure and use the `gemini-2.5-flash` model for agent runtime and testing. This model has high capacity, stable performance, and handles long contexts and multiple parallel tool calls without hitting the daily rate limits or 503 errors present on older or preview models (like `gemini-2.5-flash-lite` or `gemini-3.5-flash`).

- **Structured Data & FAQ Schema Constraints**:
  - ONLY recommend or generate FAQ structured data (`FAQPage` schema) if the site is an official authority, medical, or government portal (e.g., domains containing `.gov`, `.edu`, `nhs.uk`, `cdc.gov`).
  - If the target website is a standard blog, travel guide, commercial, or e-commerce site, do NOT mention, list, or explain FAQPage schema deprecation in your output reports. Simply recommend appropriate structured data types (e.g., `Article`, `Product`, `Review`) directly from the Google Search Gallery: `https://developers.google.com/search/docs/appearance/structured-data/search-gallery`.
  - Authoritative reference tool: When verifying structured data rules, use the `google-developer-knowledge` MCP server tools (like `answer_query` or `search_documents`) to pull the latest rules directly from Google's official developer docs.
