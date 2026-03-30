"""Build the final end-to-end demo pack from the conformance suite output."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from margin_call_demo import DemoExecutionError, _load_json, _relative_path, _utc_now, _write_json, _write_text

SCENARIO_ARTIFACT_FIELDS = [
    "policyEvaluationReportPath",
    "optimizationReportPath",
    "workflowInputPath",
    "workflowResultPath",
    "quickstartSeedReceiptPath",
    "adapterExecutionReportPath",
    "adapterStatusPath",
]


def build_final_demo_pack(
    *,
    conformance_report_path: str | Path,
    output_dir: str | Path,
    repo_root: str | Path,
) -> dict[str, Any]:
    repo_root_path = Path(repo_root).resolve()
    output_dir_path = Path(output_dir).resolve()
    output_dir_path.mkdir(parents=True, exist_ok=True)

    conformance_report = _load_json(_resolve_path(repo_root_path, conformance_report_path))
    if conformance_report["overallStatus"] != "PASS":
        raise DemoExecutionError(
            "The conformance suite must pass before the final demo pack can be built."
        )
    runtime_evidence = conformance_report["runtimeEvidence"]
    if runtime_evidence["validationFailures"]:
        raise DemoExecutionError(
            "The conformance suite runtime evidence is incomplete: "
            + "; ".join(runtime_evidence["validationFailures"])
        )

    demo_reports = [
        _load_json(repo_root_path / demo_report["reportPath"])
        for demo_report in conformance_report["demoReports"]
    ]

    final_pack_path = output_dir_path / "final-demo-pack.json"
    summary_path = output_dir_path / "final-demo-pack-summary.md"
    machine_readable_artifacts = _machine_readable_artifacts(
        repo_root=repo_root_path,
        conformance_report=conformance_report,
        demo_reports=demo_reports,
        runtime_evidence=runtime_evidence,
    )
    human_readable_artifacts = _human_readable_artifacts(
        repo_root=repo_root_path,
        conformance_report=conformance_report,
        demo_reports=demo_reports,
        runtime_evidence=runtime_evidence,
    )
    integration_surfaces = _integration_surfaces()
    readiness = _readiness_assessment(runtime_evidence=runtime_evidence)

    pack = {
        "reportType": "FinalDemoPack",
        "reportVersion": "0.1.0",
        "demoPackId": _demo_pack_id(
            conformance_report=conformance_report,
            demo_reports=demo_reports,
            integration_surfaces=integration_surfaces,
            readiness=readiness,
        ),
        "generatedAt": _utc_now(),
        "overallStatus": "PASS",
        "command": "make demo-all",
        "artifacts": {
            "finalDemoPackPath": _relative_path(final_pack_path, repo_root_path),
            "markdownSummaryPath": _relative_path(summary_path, repo_root_path),
            "conformanceReportPath": conformance_report["artifacts"]["conformanceReportPath"],
            "conformanceSummaryPath": conformance_report["artifacts"]["markdownSummaryPath"],
            "demoArtifactIndexPath": "docs/evidence/DEMO_ARTIFACT_INDEX.md",
            "integrationGuidePath": "docs/integration/THIRD_PARTY_INTEGRATION_GUIDE.md",
            "proposalReadinessPath": "docs/evidence/PROPOSAL_READINESS_ASSESSMENT.md",
            "runbookPath": "docs/runbooks/FINAL_DEMO_RUNBOOK.md",
        },
        "commandSurface": {
            "primaryQuickstartCommands": [
                runtime_evidence["deploymentCommand"],
                runtime_evidence["referenceAdapterCommand"],
                runtime_evidence["referenceAdapterStatusCommand"],
                "make demo-margin-call-quickstart",
                "make demo-substitution-quickstart",
                "make demo-return-quickstart",
                "make test-conformance",
                "make demo-all",
            ],
            "comparisonOnlyCommands": [
                "make demo-margin-call",
                "make demo-substitution",
                "make demo-return",
                "make verify-portable",
            ],
            "fullRepositoryVerificationCommands": [
                "make verify",
            ],
        },
        "runtimeEvidence": runtime_evidence,
        "demoFlows": [
            _demo_flow_entry(demo_report_entry, report)
            for demo_report_entry, report in zip(
                conformance_report["demoReports"], demo_reports, strict=True
            )
        ],
        "invariantOutput": {
            "checkCount": conformance_report["coverage"]["completedCheckCount"],
            "passedCheckCount": conformance_report["coverage"]["passedCheckCount"],
            "failedCheckCount": conformance_report["coverage"]["failedCheckCount"],
            "conformanceChecks": conformance_report["checks"],
        },
        "readiness": readiness,
        "machineReadableArtifacts": machine_readable_artifacts,
        "humanReadableArtifacts": human_readable_artifacts,
        "integrationSurfaces": integration_surfaces,
    }

    pack["machineReadableArtifacts"] = sorted(
        set(pack["machineReadableArtifacts"])
        | {_relative_path(final_pack_path, repo_root_path)}
    )
    pack["humanReadableArtifacts"] = sorted(
        set(pack["humanReadableArtifacts"])
        | {_relative_path(summary_path, repo_root_path)}
    )

    _write_json(final_pack_path, pack)
    _write_text(summary_path, _render_final_demo_summary(pack))
    return pack


def _demo_flow_entry(demo_report_entry: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    comparison_command = {
        "CONFIDENTIAL_MARGIN_CALL": "make demo-margin-call",
        "CONFIDENTIAL_COLLATERAL_SUBSTITUTION": "make demo-substitution",
        "CONFIDENTIAL_MARGIN_RETURN": "make demo-return",
    }[demo_report_entry["demoType"]]
    return {
        "demoType": demo_report_entry["demoType"],
        "reportType": demo_report_entry["reportType"],
        "runtimeMode": demo_report_entry["runtimeMode"],
        "command": demo_report_entry["command"],
        "comparisonCommand": comparison_command,
        "overallStatus": report["overallStatus"],
        "reportPath": demo_report_entry["reportPath"],
        "summaryPath": demo_report_entry["summaryPath"],
        "timelinePath": demo_report_entry["timelinePath"],
        "positiveScenarioIds": demo_report_entry["positiveScenarioIds"],
        "negativeScenarioIds": demo_report_entry["negativeScenarioIds"],
        "whatIsRealNow": _real_runtime_note(report),
        "whatRemainsStaged": _staged_runtime_note(demo_report_entry["demoType"]),
    }


def _machine_readable_artifacts(
    *,
    repo_root: Path,
    conformance_report: dict[str, Any],
    demo_reports: list[dict[str, Any]],
    runtime_evidence: dict[str, Any],
) -> list[str]:
    artifacts = {
        conformance_report["artifacts"]["conformanceReportPath"],
        conformance_report["artifacts"]["eligibilityDeterminismArtifactPath"],
        conformance_report["artifacts"]["haircutVectorArtifactPath"],
        runtime_evidence["deploymentReceiptPath"],
        runtime_evidence["referenceAdapterExecutionReportPath"],
        runtime_evidence["referenceAdapterStatusPath"],
    }

    for demo_report in demo_reports:
        for value in demo_report["artifacts"].values():
            if value is not None and value.endswith(".json"):
                artifacts.add(value)
        for scenario in demo_report["scenarios"]:
            for field in SCENARIO_ARTIFACT_FIELDS:
                value = scenario.get(field)
                if value is not None:
                    artifacts.add(value)

    for artifact in sorted(artifacts):
        if not (repo_root / artifact).is_file():
            raise DemoExecutionError(
                f"Final demo pack references a missing machine-readable artifact: {artifact}"
            )

    return sorted(artifacts)


def _human_readable_artifacts(
    *,
    repo_root: Path,
    conformance_report: dict[str, Any],
    demo_reports: list[dict[str, Any]],
    runtime_evidence: dict[str, Any],
) -> list[str]:
    artifacts = {
        conformance_report["artifacts"]["markdownSummaryPath"],
        "docs/evidence/DEMO_ARTIFACT_INDEX.md",
        "docs/evidence/PROPOSAL_READINESS_ASSESSMENT.md",
        "docs/integration/THIRD_PARTY_INTEGRATION_GUIDE.md",
        "docs/runbooks/FINAL_DEMO_RUNBOOK.md",
        runtime_evidence["deploymentSummaryPath"],
        runtime_evidence["referenceAdapterSummaryPath"],
    }

    for demo_report in demo_reports:
        for value in demo_report["artifacts"].values():
            if value is not None and value.endswith(".md"):
                artifacts.add(value)

    for artifact in sorted(artifacts):
        if not (repo_root / artifact).is_file():
            raise DemoExecutionError(
                f"Final demo pack references a missing human-readable artifact: {artifact}"
            )

    return sorted(artifacts)


def _integration_surfaces() -> list[dict[str, Any]]:
    return [
        {
            "participantType": "VENUE",
            "purpose": "Submit secured-finance obligations and consume machine-readable execution outcomes.",
            "requiredInputs": [
                "obligationId",
                "obligationAmount",
                "settlementCurrency",
                "currentPostedLotIds",
                "substitutionRequest",
            ],
            "controlPlaneOutputs": [
                "OptimizationReport",
                "ExecutionReport",
                "SubstitutionReport",
                "ReturnReport",
            ],
            "guidePath": "docs/integration/THIRD_PARTY_INTEGRATION_GUIDE.md",
        },
        {
            "participantType": "FINANCING_APP",
            "purpose": "Call policy evaluation, optimization, and workflow orchestration from a Canton-native lending or derivatives application.",
            "requiredInputs": [
                "CPL policy package",
                "inventory snapshot",
                "obligation snapshot",
                "workflow correlation id",
            ],
            "controlPlaneOutputs": [
                "PolicyEvaluationReport",
                "OptimizationReport",
                "workflow input payloads",
                "execution evidence",
            ],
            "guidePath": "docs/integration/THIRD_PARTY_INTEGRATION_GUIDE.md",
        },
        {
            "participantType": "TOKEN_ISSUER",
            "purpose": "Replace the reference adapter later by consuming workflow-declared settlement intent without taking over policy or workflow authority.",
            "requiredInputs": [
                "SettlementInstruction contract fields",
                "tokenAdapterReference",
                "assetId",
                "custody and destination accounts",
            ],
            "controlPlaneOutputs": [
                "settlement intent references",
                "execution reports",
                "audit trail evidence",
            ],
            "prototypeScope": "Today this boundary is proven by the Quickstart reference token adapter path only.",
            "guidePath": "docs/integration/THIRD_PARTY_INTEGRATION_GUIDE.md",
        },
        {
            "participantType": "CUSTODIAN",
            "purpose": "Approve or reject control changes and confirm settlement-driven encumbrance updates.",
            "requiredInputs": [
                "approval request identifiers",
                "encumbered lot ids",
                "replacement or return lot ids",
                "settlement system routing",
            ],
            "controlPlaneOutputs": [
                "approval-gated workflow states",
                "execution-report event ids",
                "audit-ready workflow steps",
            ],
            "guidePath": "docs/integration/THIRD_PARTY_INTEGRATION_GUIDE.md",
        },
    ]


def _readiness_assessment(*, runtime_evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "realOnQuickstart": [
            "Pinned Quickstart deployment and DAR installation into app-provider and app-user participants.",
            "One concrete reference token adapter posting path with machine-readable execution and status evidence.",
            "Quickstart-backed confidential margin call, substitution, and return demo flows with real workflow-to-adapter handoff evidence.",
            "Aggregate invariant evidence across those runtime-backed demo paths through make test-conformance and make demo-all.",
        ],
        "machineReadableProof": [
            runtime_evidence["deploymentReceiptPath"],
            runtime_evidence["referenceAdapterExecutionReportPath"],
            runtime_evidence["referenceAdapterStatusPath"],
            "reports/generated/margin-call-quickstart-execution-report.json",
            "reports/generated/substitution-quickstart-report.json",
            "reports/generated/return-quickstart-report.json",
            "reports/generated/conformance-suite-report.json",
            "reports/generated/final-demo-pack.json",
        ],
        "prototypeOnly": [
            "Production-grade custodian or issuer adapters beyond the narrow reference token path.",
            "Role-scoped disclosure profiles beyond the current workflow-party and provider-visible baseline.",
            "Workflow-coupled optimizer reservation and consent interfaces.",
            "Settlement-window enforcement and broader collateral business logic hardening.",
        ],
        "technicalDeltaFromEarlierPrototype": [
            "The primary demo package no longer centers IDE-ledger-only workflow runs; it now centers Quickstart deployment plus adapter-backed runtime evidence.",
            "The conformance suite now validates real Quickstart workflow, adapter, and provider-visible status artifacts rather than only the pre-Quickstart report chain.",
            "The final demo pack now distinguishes real runtime-backed proof from staged roadmap scope explicitly instead of implying parity across all integrations.",
        ],
    }


def _real_runtime_note(report: dict[str, Any]) -> str:
    positive = next(scenario for scenario in report["scenarios"] if scenario["mode"] == "POSITIVE")
    return (
        f"{report['demo']['command']} executes on Quickstart and emits "
        f"{positive['policyEvaluationReportPath']}, {positive['workflowResultPath']}, "
        f"and the adapter-backed runtime evidence for the positive path."
    )


def _staged_runtime_note(demo_type: str) -> str:
    if demo_type == "CONFIDENTIAL_MARGIN_CALL":
        return "The IDE-ledger margin-call path remains a comparison surface only; broader adapter coverage and role-scoped disclosure are still staged."
    if demo_type == "CONFIDENTIAL_COLLATERAL_SUBSTITUTION":
        return "The narrow reference adapter proves the replacement handoff, but production custodian or tri-party substitution integrations remain staged."
    return "The Quickstart return path proves one release handoff, while broader settlement-window semantics and production-grade release adapters remain staged."


def _render_final_demo_summary(pack: dict[str, Any]) -> str:
    lines = [
        "# Final Demo Pack Summary",
        "",
        f"- Demo pack ID: `{pack['demoPackId']}`",
        f"- Command: `{pack['command']}`",
        f"- Overall status: `{pack['overallStatus']}`",
        f"- Conformance report: `{pack['artifacts']['conformanceReportPath']}`",
        f"- Quickstart deployment receipt: `{pack['runtimeEvidence']['deploymentReceiptPath']}`",
        f"- Reference adapter execution report: `{pack['runtimeEvidence']['referenceAdapterExecutionReportPath']}`",
        "",
        "## Runtime Evidence",
        "",
        "| Surface | Command | Artifact |",
        "| --- | --- | --- |",
        f"| Quickstart deployment | `{pack['runtimeEvidence']['deploymentCommand']}` | `{pack['runtimeEvidence']['deploymentReceiptPath']}` |",
        f"| Reference adapter path | `{pack['runtimeEvidence']['referenceAdapterCommand']}` | `{pack['runtimeEvidence']['referenceAdapterExecutionReportPath']}` |",
        f"| Reference adapter status | `{pack['runtimeEvidence']['referenceAdapterStatusCommand']}` | `{pack['runtimeEvidence']['referenceAdapterStatusPath']}` |",
        "",
        "## Demo Flows",
        "",
        "| Demo | Report Type | Command | Runtime | Positive | Negative | Report |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for flow in pack["demoFlows"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    flow["demoType"],
                    flow["reportType"],
                    f"`{flow['command']}`",
                    flow["runtimeMode"],
                    ", ".join(flow["positiveScenarioIds"]),
                    ", ".join(flow["negativeScenarioIds"]),
                    f"`{flow['reportPath']}`",
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Real Vs Staged",
            "",
            "### Real On Quickstart",
            "",
        ]
    )

    for item in pack["readiness"]["realOnQuickstart"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "### Prototype Scope Still Staged",
            "",
        ]
    )

    for item in pack["readiness"]["prototypeOnly"]:
        lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "## Invariant Output",
            "",
            "| Check | Status | Detail |",
            "| --- | --- | --- |",
        ]
    )

    for check in pack["invariantOutput"]["conformanceChecks"]:
        lines.append(
            f"| {check['checkId']} | {check['status']} | {check['detail']} |"
        )

    lines.extend(
        [
            "",
            "## Command Surface",
            "",
            f"- Primary Quickstart commands: `{', '.join(pack['commandSurface']['primaryQuickstartCommands'])}`",
            f"- Comparison-only commands: `{', '.join(pack['commandSurface']['comparisonOnlyCommands'])}`",
            f"- Full verification commands: `{', '.join(pack['commandSurface']['fullRepositoryVerificationCommands'])}`",
            "",
            "## Integration Surfaces",
            "",
            "| Participant | Purpose | Outputs |",
            "| --- | --- | --- |",
        ]
    )

    for surface in pack["integrationSurfaces"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    surface["participantType"],
                    surface["purpose"],
                    ", ".join(surface["controlPlaneOutputs"]),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Artifact Counts",
            "",
            f"- Machine-readable artifacts: `{len(pack['machineReadableArtifacts'])}`",
            f"- Human-readable artifacts: `{len(pack['humanReadableArtifacts'])}`",
            f"- Artifact index: `{pack['artifacts']['demoArtifactIndexPath']}`",
            "",
        ]
    )

    return "\n".join(lines) + "\n"


def _demo_pack_id(
    *,
    conformance_report: dict[str, Any],
    demo_reports: list[dict[str, Any]],
    integration_surfaces: list[dict[str, Any]],
    readiness: dict[str, Any],
) -> str:
    canonical = json.dumps(
        {
            "conformanceSuiteId": conformance_report["suiteId"],
            "demoReportIds": [
                next(
                    report[key]
                    for key in (
                        "executionId",
                        "substitutionReportId",
                        "returnReportId",
                    )
                    if key in report
                )
                for report in demo_reports
            ],
            "integrationSurfaces": integration_surfaces,
            "readiness": readiness,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"fdp-{digest[:16]}"


def _resolve_path(repo_root: Path, candidate: str | Path) -> Path:
    candidate_path = Path(candidate)
    if candidate_path.is_absolute():
        return candidate_path
    return (repo_root / candidate_path).resolve()
