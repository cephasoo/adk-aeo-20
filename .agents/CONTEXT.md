# Secure Coding Standards & Paved Roads

## 1. Tool Input Validation
* Every tool MUST enforce strict Pydantic inputs. No raw inputs or dictionaries without schema parsing.
* Validate all ranges, types, and permissions before execution.

## 2. No Shell Execution
* Do not run raw command lines or invoke subprocess tools unless explicitly whitelisted.
* Any terminal execution MUST be validated against the IDE PreToolUse hooks.

## 3. Pre-Commit Gating & Remediation Loop
* Code MUST pass local Semgrep scans before commit.
* If a commit fails due to a security violation (e.g., hardcoded API key):
  1. Locate the file and line number from the pre-commit stdout.
  2. Remediation: Refactor the code (e.g. replace hardcoded key with `os.environ.get("GEMINI_API_KEY")`).
  3. Re-stage the files and run git commit again.
  4. Never use `--no-verify`.

## 4. TDD Planning Gate
During the Plan phase, you must decompose the workspace task into logical, modular stages. Every implementation plan MUST include a dedicated **Security Boundaries & Assertions** section outlining specific edge cases that could exploit the feature.
