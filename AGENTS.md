# AGENTS.md

Purpose
- Ensure all agents record any technical debt they create or discover in DEBT.md, with an approximate USD cost to fix it.

Required behavior
- Always create or update an entry in DEBT.md immediately when:
    - introducing a shortcut, hack, or incomplete work that causes technical debt, or
    - discovering existing technical debt during work or review.
- Include a reasonable estimated dollar cost to remediate (see Estimation Guidelines).
- Reference the committing PR/commit and open a tracker issue when appropriate.

DEBT.md entry format (required fields)
- ID: DEBT-YYYY-NNN
- Title: short summary
- Date: YYYY-MM-DD
- Found by: <agent/team/automation>
- Source: {new-code, review, legacy, third-party}
- Description: concise technical description of the debt
- Impact: what fails or is at risk (performance, reliability, security, maintainability)
- Root cause: why it exists
- Severity: {Trivial, Small, Medium, Large, Critical}
- Estimated Cost (USD): $X (approximate)
- Confidence: {Low, Medium, High}
- Proposed Fix: high-level remediation steps
- Status: {open, in-progress, deferred, fixed}

Estimation guidelines (approx ranges)
- Trivial: $50–$200
- Small: $200–$2,000
- Medium: $2,000–$20,000
- Large: $20,000–$200,000
- Critical: > $200,000
- Note: these are starting points. Adjust for local rates, required testing, rollout & coordination. Mark Confidence accordingly.

Workflow (minimum)
1. Add or update an entry in DEBT.md with required fields and Estimated Cost.
2. Reference the DEBT ID in the commit/PR message (e.g., "Introduce X (DEBT-2025-001)").

Review and maintenance
- Every PR that introduces non-trivial shortcuts must identify any new debt and update DEBT.md before merge.
- During code review, reviewers must add any discovered debt to DEBT.md.
- Periodic triage (monthly/quarterly) should review DEBT.md entries, update costs/confidence, reassign priorities.

Example entry
```
ID: DEBT-2025-001
Title: Incomplete retry logic for external API
Date: 2025-09-17
Found by: build-agent
Source: new-code
Description: Retry logic retries once without backoff; missing idempotency checks.
Impact: Increased failures under load; potential duplicate operations.
Root cause: Timeboxed implementation during sprint.
Severity: Medium
Estimated Cost (USD): $7,500
Confidence: Medium
Proposed Fix: Implement exponential backoff + idempotency tokens, add integration tests, update docs.
Owner: payments-team
Status: open
Related: PR #123, commit abcdef
```

Compliance
- Agents that fail to record created or discovered technical debt must be flagged for review; recording is mandatory.

Keep entries factual, concise, and kept up to date.