---
name: manage-aeo-custom-blocks
description: Rebuild, deploy, and configure custom Gutenberg blocks (nav, footer, form, alert, etc.) for Sonnet and Prose AEO and Technical SEO page optimization.
---

# AEO Custom Blocks Management Skill

Use this skill to manage, compile, deploy, and integrate the custom React Gutenberg blocks built for **Sonnet and Prose** (formerly Coalition Technologies).

---

## 1. Compilation & Deployment

The blocks are written in React (JSX) and Sass (SCSS) and must be compiled into standard browser-compatible assets and copied to the local WordPress installation.

### Trigger Deployment Script
*   **Procedural Script**: `scripts/deploy.py`
*   **Command**: `python .agents/skills/manage-aeo-custom-blocks/scripts/deploy.py`
*   *Note*: This automatically installs Node packages, builds the React components, and deploys files to the target LocalWP plugins directory:
    `C:\Users\USER\Local Sites\aeo-copilot\app\public\wp-content\plugins\aeo-custom-blocks`

---

## 2. Block Profiles & Attributes

When programmatically editing post contents or templates, use these block names and JSON schemas:

### A. Navigation Menu (`aeo-custom-blocks/nav`)
*   **Database Tag**: `<!-- wp:aeo-custom-blocks/nav /-->`
*   **Attributes**:
    *   `brandText` (string): Text logo. Default: `"aeo-copilot"`.
    *   `ctaText` (string): Button label. Default: `"Take a Tour"`.
    *   `ctaUrl` (string): Button hyperlink target.
    *   `links` (array of link objects): `{ "label": string, "url": string }`.
*   *Integration Note*: Automatically registered site-wide via the PHP `wp_body_open` hook.

### B. Dynamic Footer (`aeo-custom-blocks/footer`)
*   **Database Tag**: `<!-- wp:aeo-custom-blocks/footer /-->`
*   *Integration Note*: Automatically enqueued globally via the PHP `wp_footer` hook. Includes a pulsing green System Status badge.

### C. Generic Form Builder (`aeo-custom-blocks/form`)
*   **Database Tag**: `<!-- wp:aeo-custom-blocks/form /-->`
*   **Attributes**:
    *   `formTitle` (string): Header title. Default: `"Request a Tour"`.
    *   `formSubtitle` (string): Header subtitle.
    *   `submitText` (string): Submit button text. Default: `"Send Request"`.
    *   `fields` (array of objects): Repeater fields containing:
        *   `id` (string): Unique identifier (e.g. `work_email`).
        *   `type` (string): `text` \| `email` \| `tel` \| `select` \| `textarea` \| `file`.
        *   `label` (string): Input label text.
        *   `placeholder` (string): Placeholder text.
        *   `required` (boolean): Enforces browser-native validation.
        *   `options` (string): Comma-separated list (required only if type is `select`).

### D. Alert Status Banner (`aeo-custom-blocks/alert`)
*   **Database Tag**: `<!-- wp:aeo-custom-blocks/alert {"type":"warning","message":"...", "dismissible":true} /-->`
*   **Attributes**:
    *   `type` (string): State theme: `success` \| `info` \| `warning` \| `error`.
    *   `message` (string): Alert text. Supports HTML links.
    *   `dismissible` (boolean): Toggles frontend close button (`&times;`) that fades out the banner.

---

## 3. Programmatic Block Insertion (Python REST API)

To insert a block onto an active WordPress page (e.g., Page 10), use the following Python REST client snippet:

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv(".env")
wp_url = os.environ.get("WP_API_URL")
auth = (os.environ.get("WP_USERNAME"), os.environ.get("WP_APPLICATION_PASSWORD"))

page_id = 10
# 1. Fetch current content
resp = requests.get(f"{wp_url}/pages/{page_id}", auth=auth, params={"context": "edit"})
page_data = resp.json()
current_content = page_data.get("content", {}).get("raw", "")

# 2. Append block markup comments
alert_block = '<!-- wp:aeo-custom-blocks/alert {"type":"warning","message":"Important Alert!","dismissible":true} /-->'
new_content = current_content + "\n\n" + alert_block

# 3. Update page content
requests.post(f"{wp_url}/pages/{page_id}", auth=auth, json={"content": new_content})
```

---

## 4. Design Guidelines (Maintaining Visual Cohesion)

*   **Dark Glassmorphism**: Containers must use translucent slate backgrounds (`rgba(15, 23, 42, 0.95)`) with backdrop filtering (`backdrop-filter: blur(12px)`).
*   **Contrast Compliance**: Text in blocks must use high-contrast foregrounds (`#f1f5f9` or `#ffffff`) to remain readable when placed on light page sections.
*   **Breathing Room**: Keep the vertical content spacing of `4.5rem` (`72px`) intact between main content blocks and footers/headers (defined in `.wp-block-post-content`).

---

## 5. Architectural Decision: Native Blocks vs. Custom Blocks

To maintain a clean, lightweight DOM and prevent block bloating, follow this decision tree when designing layouts:

| Use Case | Recommended Block Type | Rationale / Reference |
| :--- | :--- | :--- |
| Standard Body Text, Lists, Tables, or Images | **Native Blocks** (`core/paragraph`, `core/heading`, `core/list`, `core/table`, `core/image`) | Zero overhead, native styling alignment, and highly structured SEO parsing. Refer to [native_blocks.md](file:///C:/Users/USER/secure-agent-lab/gutenberg-aeo-copilot/.agents/skills/manage-aeo-custom-blocks/references/native_blocks.md). |
| Standard Grid Sections & Layout Structuring | **Native Containers** (`core/group`, `core/columns`) | Native groups allow specifying semantic HTML5 tags (like `<section>`, `<main>`) in their block settings panel. |
| Global Site Header & Nav Menu | **Custom Nav Block** (`aeo-custom-blocks/nav`) | Dynamic wordpress classic/block menu resolving, administrative offsets, and a responsive glassmorphic mobile drawer. |
| Site-wide Footer & Status Badge | **Custom Footer Block** (`aeo-custom-blocks/footer`) | Automated rendering across all pages via `wp_footer` hook with cohesive glassmorphic styling and active status badge. |
| Dynamic Contact/Feedback Forms | **Custom Form Block** (`aeo-custom-blocks/form`) | Fully customizable form builder inputs, file uploads, dropdowns, and dynamic inline Ajax loading/success banner feedback. |
| Dismissible Notification Banners | **Custom Alert Block** (`aeo-custom-blocks/alert`) | Dynamic client-side fade-out dismiss actions and WCAG contrast-compliant glassmorphism state overrides. |
| Dynamic FAQ Accordions | **Custom FAQ Block** (`aeo-custom-blocks/faq`) | Output semantic HTML5 `<details>` and `<summary>` tags to optimize featured snippet indexing. |

---

## 6. Real-world Block Insertion Examples

Review the examples folder to see how raw HTML is modified when appending a custom Gutenberg block:
*   **Original State (Before Insertion)**: See [before_insert.html](file:///C:/Users/USER/secure-agent-lab/gutenberg-aeo-copilot/.agents/skills/manage-aeo-custom-blocks/examples/before_insert.html)
*   **Modified State (After Insertion)**: See [after_insert.html](file:///C:/Users/USER/secure-agent-lab/gutenberg-aeo-copilot/.agents/skills/manage-aeo-custom-blocks/examples/after_insert.html)
