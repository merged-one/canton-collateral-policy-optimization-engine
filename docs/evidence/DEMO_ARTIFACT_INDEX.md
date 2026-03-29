# Demo Artifact Index

## Purpose

This index identifies the real artifact bundle produced by the final prototype demo surface. It is the reviewer-facing map from commands to generated evidence.

## Primary Commands

```sh
make test-conformance
make demo-all
```

## Aggregate Artifacts

| Artifact | Type | Produced By | Purpose |
| --- | --- | --- | --- |
| `reports/generated/conformance-suite-report.json` | JSON | `make test-conformance` | machine-readable invariant pass or fail output across all three confidential demos |
| `reports/generated/conformance-suite-summary.md` | Markdown | `make test-conformance` | human-readable summary of the aggregate conformance checks |
| `reports/generated/conformance-eligibility-determinism-policy-evaluation-report.json` | JSON | `make test-conformance` | supporting determinism evidence for repeated policy evaluation |
| `reports/generated/conformance-haircut-policy-evaluation-report.json` | JSON | `make test-conformance` | supporting haircut-vector evidence for lendable-value arithmetic |
| `reports/generated/final-demo-pack.json` | JSON | `make demo-all` | machine-readable package index for the final prototype demonstration |
| `reports/generated/final-demo-pack-summary.md` | Markdown | `make demo-all` | operator and reviewer summary of the final prototype package |

## Confidential Workflow Demo Artifacts

### Margin Call

- `reports/generated/margin-call-demo-execution-report.json`
- `reports/generated/margin-call-demo-summary.md`
- `reports/generated/margin-call-demo-timeline.md`
- `reports/generated/positive-margin-call-policy-evaluation-report.json`
- `reports/generated/positive-margin-call-optimization-report.json`
- `reports/generated/positive-margin-call-workflow-input.json`
- `reports/generated/positive-margin-call-workflow-result.json`

### Collateral Substitution

- `reports/generated/substitution-demo-report.json`
- `reports/generated/substitution-demo-summary.md`
- `reports/generated/substitution-demo-timeline.md`
- `reports/generated/positive-substitution-policy-evaluation-report.json`
- `reports/generated/positive-substitution-optimization-report.json`
- `reports/generated/positive-substitution-workflow-input.json`
- `reports/generated/positive-substitution-workflow-result.json`
- negative substitution policy, optimization, workflow input, and workflow result artifacts for ineligibility, concentration breach, unauthorized release, and partial substitution

### Margin Return

- `reports/generated/return-demo-report.json`
- `reports/generated/return-demo-summary.md`
- `reports/generated/return-demo-timeline.md`
- `reports/generated/positive-return-policy-evaluation-report.json`
- `reports/generated/positive-return-optimization-report.json`
- `reports/generated/positive-return-workflow-input.json`
- `reports/generated/positive-return-workflow-result.json`
- negative return policy, optimization, workflow input, and workflow result artifacts for unauthorized release, replay, and obligation-state mismatch

## Supporting Documentation

The final demo package should be read together with:

- `docs/testing/CONFORMANCE_SUITE.md`
- `docs/runbooks/FINAL_DEMO_RUNBOOK.md`
- `docs/integration/THIRD_PARTY_INTEGRATION_GUIDE.md`
- `docs/evidence/prompt-12-execution-report.md`

## Reviewer Workflow

1. run `make demo-all`
2. inspect `reports/generated/final-demo-pack.json`
3. inspect `reports/generated/conformance-suite-report.json`
4. inspect the three confidential workflow report artifacts
5. inspect the integration guide and this artifact index

The package is only valid if the machine-readable artifacts, Markdown summaries, and command surface all line up with one another.
