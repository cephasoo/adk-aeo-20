# Native WordPress Gutenberg Blocks Registry

This reference registry documents the core Gutenberg blocks supported natively by WordPress. The Gutenberg Copilot agent uses this mapping to determine if a requested layout can be built out-of-the-box using core components or if it requires compiling a custom React block.

---

## 📦 1. Text & Semantic Blocks

### Paragraph (`core/paragraph`)
*   **Purpose**: Default body text wrapper.
*   **HTML Output**: `<p>...</p>`
*   **Attributes**: alignment, fontSize, textColor, backgroundColor.

### Heading (`core/heading`)
*   **Purpose**: Semantic section dividers.
*   **HTML Output**: `<h1-h6>...</h1-h6>`
*   **Attributes**: level (1-6), textAlign, placeholder.
*   **AEO Note**: Key for heading hierarchies. Always nested sequentially (no skipping levels).

### List (`core/list`) & List Item (`core/list-item`)
*   **Purpose**: Bulleted or numbered listings.
*   **HTML Output**: `<ul><li>...</li></ul>` or `<ol><li>...</li></ol>`
*   **AEO Note**: Highly valuable for search summaries and featured snippets.

### Table (`core/table`)
*   **Purpose**: Tabular structured data.
*   **HTML Output**: `<table><thead><tr><th>...</th></tr></thead><tbody>...</tbody></table>`
*   **AEO Note**: Excellent for data transparency. LLMs parse tables easily.

---

## 🖼️ 2. Media Blocks

### Image (`core/image`)
*   **Purpose**: Embedded images.
*   **HTML Output**: `<figure class="wp-block-image"><img src="..." alt="..." /></figure>`
*   **AEO Note**: **Alt tags are mandatory** for indexing and accessibility audits.

---

## 🧱 3. Layout & Container Blocks

### Group (`core/group`)
*   **Purpose**: Container to group multiple blocks together.
*   **HTML Output**: `<div class="wp-block-group">...</div>` (or custom HTML element tag like `<section>`, `<header>`, `<aside>`, `<main>`).
*   **AEO Note**: Can be configured in block settings to render as a semantic tag (e.g. `<section>`), helping clean up HTML layouts.

### Columns (`core/columns`) & Column (`core/column`)
*   **Purpose**: Multi-column responsive grids.
*   **HTML Output**: Flexbox-based grids.

---

## 🛠️ 4. Action Blocks

### Buttons (`core/buttons`) & Button (`core/button`)
*   **Purpose**: Call-To-Action (CTA) link buttons.
*   **HTML Output**: `<div class="wp-block-buttons"><div class="wp-block-button"><a class="wp-block-button__link">...</a></div></div>`
