# Project Rules

- **Gemini Model Choice**: Always configure and use the `gemini-2.5-flash` model for agent runtime and testing. This model has high capacity, stable performance, and handles long contexts and multiple parallel tool calls without hitting the daily rate limits or 503 errors present on older or preview models (like `gemini-2.5-flash-lite` or `gemini-3.5-flash`).

- **Structured Data & Schema Recommendations**:
  - Suggest appropriate structured data types matching the page intent (e.g., `Article`, `Product`, `Review`, `LocalBusiness`) by referencing Google's official Search Gallery: `https://developers.google.com/search/docs/appearance/structured-data/search-gallery`.
  - Avoid listing, discussing, or explaining irrelevant or non-applicable schema types in your reports.
