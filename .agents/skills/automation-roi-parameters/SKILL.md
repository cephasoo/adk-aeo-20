---
name: automation-roi-parameters
description: Defines default financial parameters, manual labor rates, weekly hour baselines, and efficiency multipliers for calculating ROI on Marketing and Agentic Automation systems.
---

# Automation ROI Parameters Configuration

This project-scoped skill registers the official financial and operational parameters used to calculate time and cost savings for **Sonnet and Prose** automation systems (specifically for the interactive ROI Calculator block).

---

## 1. Baseline Financial & Operational Constants

Do not hard-code constants in the prompt. Load and parse the values dynamically from the resource file:
*   **Constants Resource**: [roi_constants.json](file:///C:/Users/USER/secure-agent-lab/gutenberg-aeo-copilot/.agents/skills/automation-roi-parameters/resources/roi_constants.json)

---

## 2. ROI Savings Calculation Engine

To prevent mathematical calculation hallucinations, delegates all calculations to the python script:
*   **Procedural Script**: [calculate_roi.py](file:///C:/Users/USER/secure-agent-lab/gutenberg-aeo-copilot/.agents/skills/automation-roi-parameters/scripts/calculate_roi.py)
*   **Usage**:
    `python .agents/skills/automation-roi-parameters/scripts/calculate_roi.py [weekly_manual_hours] [average_hourly_rate]`

### Example Execution:
Run with defaults:
`python .agents/skills/automation-roi-parameters/scripts/calculate_roi.py`
Output:
```json
{
  "weekly_savings": 1700,
  "annual_savings": 85900,
  "hours_reclaimed": 1040,
  "hours_input": 25.0,
  "rate_input": 85.0
}
```
Use this script's JSON output for formatting values inside content block builders.
