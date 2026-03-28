# Change Control

## Purpose

Change control keeps a safety-critical prototype from drifting into undocumented behavior. Every change should be proportional to its risk and should leave behind evidence.

## Change Classes

| Class | Description | Required Artifacts |
| --- | --- | --- |
| Class 0 | Documentation-only change with no behavior impact. | worklog update, reproducible command, verification output |
| Class 1 | Interface, schema, or invariant change with future behavior impact. | Class 0 artifacts plus invariant updates and usually an ADR |
| Class 2 | Workflow, security, or economic-logic change. | Class 1 artifacts plus threat-model, risk, and test updates |
| Class 3 | Demo or release-path change. | Class 2 artifacts plus demo evidence and release checklist review |

## Standard Flow

1. Read `AGENTS.md` and `MASTER_TRACKER.md`.
2. Record a pre-change worklog entry.
3. Make the smallest coherent change.
4. Update invariants, ADRs, evidence, risks, and runbooks as required.
5. Run reproducible verification commands.
6. Record the post-change worklog entry and results.

## Repository-Specific Rules

- No fake demo outputs in the main execution path.
- Separate policy, optimization, workflow execution, and reporting.
- Pin dependencies before relying on them for demo or release flows.
- Treat substitution and release handling as high-risk workflow areas.
