---
name: hidden-schema-compliance-auditor
description: Detects hidden FAQPage schemas and recommends semantic structural layout fixes (such as rewriting plain text sections into visible question-and-answer headings).
---

# Skill: hidden-schema-compliance-auditor

## Description
Detects hidden FAQPage schemas and recommends semantic structural layout fixes (such as rewriting plain text sections into visible question-and-answer headings).

## Operational Workflow

### 1. Execute the Compliance Tool
When auditing a page's SEO schemas, always call the `audit_hidden_faq_schema` tool.
*   If the tool returns `compliance_score: "100.0%"`, document the result as a pass.
*   If the tool returns any violations, flag the page as **High Risk: Hidden Structured Data Violation**.

### 2. Diagnose Mismatch Severity
*   **Case A: True Mismatches (Spam):** If the schema contains information that is completely absent on-page (e.g. promotional text, hidden pricing structures, unrelated keywords), flag this as an intentional search engine optimization guideline violation.
*   **Case B: Formatting Mismatches:** If the schema matches on-page facts but uses different phrasing, it is a semantic gap.

### 3. Apply the Remediation Blueprint
If the compliance score is under 100%, do not just advise deleting the schema. Recommend these structural layout remedies:

#### Remedy Action A: Delete Deprecated Schemas
Advise deleting the `FAQPage` JSON-LD schema block completely, as search engines (specifically Google) have deprecated organic FAQ rich snippets. There is no longer an organic ranking incentive to justify keeping it.

#### Remedy Action B: Transition to Conversational NLP Layouts
Instruct the user to take the valuable questions and answers from the deprecated schema and place them directly in the visible body copy using conversational headings:
1.  **Format headings as questions:** E.g., change `## Blackboard Support` to `## Does our system integrate with Blackboard?`
2.  **Define answers cleanly:** The paragraph immediately following the heading must start with a direct, unambiguous statement matching the conversational search pattern of AI engines.
3.  *Provide the user with exact rewritten layout examples.*
