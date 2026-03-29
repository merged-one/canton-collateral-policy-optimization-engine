# Test Surface

This directory contains deterministic policy-engine tests and remains the home for future conformance and integration coverage.

Current contents:

- `test/conformance/` for the aggregate conformance suite that verifies invariant pass or fail output across the confidential workflow demos
- `test/policy-engine/` for the `CPL v0.1` policy engine scenario suite
- `test/optimizer/` for deterministic best-to-post, substitution, concentration, and no-solution scenarios
- `make demo-margin-call` as the current executable conformance path for end-to-end positive and negative margin-call scenarios
- `make demo-substitution` as the executable conformance path for end-to-end positive and negative substitution scenarios
- `make test-conformance` as the aggregate invariant-verification path across margin call, substitution, and return

Expected future contents:

- Daml package tests
- policy-engine determinism tests
- optimizer determinism tests
- report-contract validation tests
- conformance scenarios against LocalNet or an equivalent pinned runtime
