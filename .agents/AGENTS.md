# Project Rules

- **Gemini Model Choice**: Always configure and use the `gemini-2.5-flash` model for agent runtime and testing. This model has high capacity, stable performance, and handles long contexts and multiple parallel tool calls without hitting the daily rate limits or 503 errors present on older or preview models (like `gemini-2.5-flash-lite` or `gemini-3.5-flash`).
