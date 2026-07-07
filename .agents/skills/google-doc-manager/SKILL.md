---
name: google-doc-manager
description: Reads, creates, and formats documents in Google Docs, providing document sharing links and appending or replacing text blocks.
---

# Skill: google-doc-manager

## Overview

> [!IMPORTANT]
> **CRITICAL ARCHITECTURAL REQUIREMENT:** Do NOT use the Google Docs API (`docs.googleapis.com`) or call `build('docs', 'v1', ...)` directly. The GCP project only has the **Google Drive API** enabled.
> 
> You can perform all document operations (create, read, append, update) through two methods:
> 
> ### Method A: Direct MCP Tools (Preferred Globally)
> If you have the `google-docs-mcp` server connected in your environment, invoke these MCP tools directly:
> *   `create_doc(title, allow_duplicates=False)` — Creates a new Google Doc (or reuses existing if `allow_duplicates=False` to prevent duplicates) and returns the ID and URL.
> *   `read_doc(document_id_or_title)` — Reads the plain text body of the Google Doc.
> *   `append_doc(document_id_or_title, text)` — Appends markdown content to the Google Doc.
> *   `update_doc(document_id_or_title, new_content)` — Replaces the entire Google Doc body with formatted markdown/mermaid diagrams.
> *   `update_doc_from_file(document_id_or_title, file_path)` — Overwrites the Google Doc with a local file content (safely handles large payloads).
> *   `append_doc_from_file(document_id_or_title, file_path)` — Appends local file content to the Google Doc (safely handles large payloads).
> 
> ### Method B: Python Library (Local Workspace Fallback)
> If you are running code locally in the `gutenberg-aeo-copilot` workspace, import the native helper library:
> `from app.tools.google_docs_native import create_google_doc, read_google_doc, update_google_doc, append_to_google_doc, update_google_doc_from_file, append_to_google_doc_from_file`

## Description
Reads, creates, and formats documents in Google Docs, providing document sharing links and appending or replacing text blocks.

## Operational Workflow

### 1. Document Identification and Resolution
When requested to manage or review Google Docs:
*   Identify whether the user provided a Document ID (a long alphanumeric string) or a Document Title.
*   The underlying tools will automatically resolve Document Titles to Document IDs via Google Drive search where applicable.

### 2. Read and Extract Text
When requested to analyze or review a Google Doc:
1. Call `read_google_doc` using the document ID or Title.
2. Retrieve the textual body copy and perform the requested analysis.

### 3. Create or Update Documents
When requested to create notes, export results, or update existing roadmaps:
*   **Creation**: Call `create_google_doc` with an appropriate title. By default, it checks for existing files to prevent duplicates. Set `allow_duplicates=True` if you explicitly need to create a duplicate. Extract the document ID and URL from the response.
*   **Appends**: Call `append_to_google_doc` (or `append_to_google_doc_from_file` for large inputs) to add new sections at the end of the document.
*   **Full Content Updates**: Call `update_google_doc` (or `update_google_doc_from_file` for large inputs) to completely replace the document body with new formatted text.
