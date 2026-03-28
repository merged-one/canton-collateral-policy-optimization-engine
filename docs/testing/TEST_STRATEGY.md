# Test Strategy

## Purpose

Testing in this repository exists to prove invariants, not just to increase coverage numbers. Each meaningful feature should map to explicit invariants and reproducible checks.

## Test Layers

1. Document checks
   Verify required control documents, sections, and cross-links exist.
2. Schema and contract tests
   Validate policy, asset, and report structures once they exist.
3. Determinism tests
   Check policy evaluation, haircuting, and optimization reproducibility.
4. Workflow tests
   Check atomicity, authorization, substitution, return, and replay behavior.
5. Security tests
   Check access control, confidentiality boundaries, and integrity assumptions.
6. Demo verification
   Check that operator-facing demo flows are backed by real commands and generated artifacts.

## Current Baseline

At this phase, the repository only supports lightweight documentation checks:

```sh
make docs-lint
make verify
```

## Traceability Expectations

- every new feature updates the invariant registry
- every invariant gains at least one planned or implemented verification hook
- every demo artifact must point back to the code path and command that generated it
