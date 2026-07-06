---
name: google-doc-manager
description: Reads, creates, and formats documents in Google Docs, providing document sharing links and appending or replacing text blocks.
---

# Skill: google-doc-manager

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
*   **Creation**: Call `create_google_doc` with an appropriate title. Extract the document ID and URL from the response.
*   **Appends**: Call `append_to_google_doc` to add new sections at the end of the document.
*   **Full Content Updates**: Call `update_google_doc` to completely replace the document body with new formatted text.
