"""Aggregate conformance suite for the final prototype demo surface."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from margin_call_demo import (
    DemoExecutionError,
    _load_json,
    _relative_path,
    _utc_now,
    _validate_json_schema,
    _write_json,
    _write_text,
    run_margin_call_demo,
)
from return_demo import run_return_demo
from substitution_demo import run_substitution_demo


APP_DIR = Path(__file__).resolve().parents[1]
POLICY_ENGINE_DIR = APP_DIR / "policy-engine"

if str(POLICY_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(POLICY_ENGINE_DIR))

from evaluator import evaluate_policy, write_report as write_policy_report  # noqa: E402


DEFAULT_MARGIN_CALL_MANIFEST = "examples/demo-scenarios/margin-call/demo-config.json"
DEFAULT_SUBSTITUTION_MANIFEST = "examples/demo-scenarios/substitution/demo-config.json"
DEFAULT_RETURN_MANIFEST = "examples/demo-scenarios/return/demo-config.json"
REQUIRED_CHECK_IDS = [
    "AUTHORIZATION_AND_ROLE_CONTROL",
    "ELIGIBILITY_DETERMINISM",
    "HAIRCUT_CORRECTNESS",
    "NO_DOUBLE_ENCUMBRANCE",
    "ATOMIC_SUBSTITUTION_WHEN_REQUIRED",
    "REPLAY_SAFETY",
    "REPORT_FIDELITY",
    "AUDIT_TRAIL_COMPLETENESS",
]


def run_conformance_suite(
    *,
    output_dir: str | Path,
    repo_root: str | Path,
    margin_call_manifest: str | Path = DEFAULT_MARGIN_CALL_MANIFEST,
    substitution_manifest: str | Path = DEFAULT_SUBSTITUTION_MANIFEST,
    return_manifest: str | Path = DEFAULT_RETURN_MANIFEST,
) -> dict[str, Any]:
    repo_root_path = Path(repo_root).resolve()
    output_dir_path = Path(output_dir).resolve()
    output_dir_path.mkdir(parents=True, exist_ok=True)

    margin_call_report = run_margin_call_demo(
        manifest_path=_resolve_path(repo_root_path, margin_call_manifest),
        output_dir=output_dir_path,
        repo_root=repo_root_path,
    )
    substitution_report = run_substitution_demo(
        manifest_path=_resolve_path(repo_root_path, substitution_manifest),
        output_dir=output_dir_path,
        repo_root=repo_root_path,
    )
    return_report = run_return_demo(
        manifest_path=_resolve_path(repo_root_path, return_manifest),
        output_dir=output_dir_path,
        repo_root=repo_root_path,
    )

    determinism_artifact = _build_determinism_artifact(
        repo_root=repo_root_path,
        output_dir=output_dir_path,
    )
    haircut_artifact = _build_haircut_artifact(
        repo_root=repo_root_path,
        output_dir=output_dir_path,
    )

    demo_reports = [margin_call_report, substitution_report, return_report]
    checks = [
        _check_authorization_and_role_control(
            substitution_report=substitution_report,
            return_report=return_report,
        ),
        _check_eligibility_determinism(determinism_artifact=determinism_artifact),
        _check_haircut_correctness(haircut_artifact=haircut_artifact),
        _check_no_double_encumbrance(
            margin_call_report=margin_call_report,
            substitution_report=substitution_report,
            return_report=return_report,
        ),
        _check_atomic_substitution_when_required(
            substitution_report=substitution_report,
        ),
        _check_replay_safety(return_report=return_report),
        _check_report_fidelity(
            demo_reports=demo_reports,
            repo_root=repo_root_path,
        ),
        _check_audit_trail_completeness(demo_reports=demo_reports),
    ]

    overall_status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    report_path = output_dir_path / "conformance-suite-report.json"
    summary_path = output_dir_path / "conformance-suite-summary.md"

    report = {
        "reportType": "ConformanceSuiteReport",
        "reportVersion": "0.1.0",
        "suiteId": _suite_id(
            checks=checks,
            demo_reports=demo_reports,
            determinism_artifact=determinism_artifact,
            haircut_artifact=haircut_artifact,
        ),
        "generatedAt": _utc_now(),
        "overallStatus": overall_status,
        "command": "make test-conformance",
        "artifacts": {
            "conformanceReportPath": _relative_path(report_path, repo_root_path),
            "markdownSummaryPath": _relative_path(summary_path, repo_root_path),
            "eligibilityDeterminismArtifactPath": determinism_artifact["artifactPath"],
            "haircutVectorArtifactPath": haircut_artifact["artifactPath"],
        },
        "coverage": {
            "requiredCheckIds": REQUIRED_CHECK_IDS,
            "completedCheckCount": len(checks),
            "passedCheckCount": sum(1 for check in checks if check["status"] == "PASS"),
            "failedCheckCount": sum(1 for check in checks if check["status"] != "PASS"),
            "totalScenarioCount": sum(report["demo"]["scenarioCount"] for report in demo_reports),
            "positiveScenarioCount": sum(
                report["demo"]["positiveScenarioCount"] for report in demo_reports
            ),
            "negativeScenarioCount": sum(
                report["demo"]["negativeScenarioCount"] for report in demo_reports
            ),
        },
        "demoReports": [
            _demo_report_entry(
                demo_type="CONFIDENTIAL_MARGIN_CALL",
                report_type="ExecutionReport",
                report=margin_call_report,
                report_path_key="executionReportPath",
            ),
            _demo_report_entry(
                demo_type="CONFIDENTIAL_COLLATERAL_SUBSTITUTION",
                report_type="SubstitutionReport",
                report=substitution_report,
                report_path_key="substitutionReportPath",
            ),
            _demo_report_entry(
                demo_type="CONFIDENTIAL_MARGIN_RETURN",
                report_type="ReturnReport",
                report=return_report,
                report_path_key="returnReportPath",
            ),
        ],
        "checks": checks,
    }

    _write_json(report_path, report)
    _write_text(summary_path, _render_conformance_summary(report))

    if overall_status != "PASS":
        failed_checks = [
            check["checkId"] for check in checks if check["status"] != "PASS"
        ]
        raise DemoExecutionError(
            "Conformance suite produced one or more failures: "
            + ", ".join(failed_checks)
        )

    return report


def _build_determinism_artifact(
    *,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    policy = _load_json(repo_root / "examples/policies/central-bank-style-policy.json")
    inventory = _load_json(repo_root / "examples/inventory/central-bank-eligible-inventory.json")

    first = evaluate_policy(copy.deepcopy(policy), copy.deepcopy(inventory))
    second = evaluate_policy(copy.deepcopy(policy), copy.deepcopy(inventory))

    artifact_path = output_dir / "conformance-eligibility-determinism-policy-evaluation-report.json"
    write_policy_report(first, artifact_path)
    _validate_json_schema(
        report_path=artifact_path,
        schema_path=repo_root / "reports/schemas/policy-evaluation-report.schema.json",
    )

    return {
        "artifactPath": _relative_path(artifact_path, repo_root),
        "firstReport": first,
        "secondReport": second,
        "matchesRepeatEvaluation": first == second,
    }


def _build_haircut_artifact(
    *,
    repo_root: Path,
    output_dir: Path,
) -> dict[str, Any]:
    policy = _relaxed_policy(
        _load_json(repo_root / "examples/policies/central-bank-style-policy.json")
    )
    inventory = _load_json(repo_root / "examples/inventory/central-bank-eligible-inventory.json")
    inventory["candidateLots"] = [copy.deepcopy(inventory["candidateLots"][0])]
    lot = inventory["candidateLots"][0]
    lot["marketValue"] = 400000.0
    lot["nominalValue"] = 420000.0
    lot["outstandingPrincipal"] = 410000.0
    lot["residualMaturityDays"] = 540

    report = evaluate_policy(policy, inventory)
    asset = _asset_result(report, lot["lotId"])
    artifact_path = output_dir / "conformance-haircut-policy-evaluation-report.json"
    write_policy_report(report, artifact_path)
    _validate_json_schema(
        report_path=artifact_path,
        schema_path=repo_root / "reports/schemas/policy-evaluation-report.schema.json",
    )

    return {
        "artifactPath": _relative_path(artifact_path, repo_root),
        "report": report,
        "asset": asset,
        "expectedValuationBasisValue": 400000.0,
        "expectedBaseHaircutBps": 600,
        "expectedTotalHaircutBps": 600,
        "expectedLendableValue": 376000.0,
    }


def _check_authorization_and_role_control(
    *,
    substitution_report: dict[str, Any],
    return_report: dict[str, Any],
) -> dict[str, Any]:
    unauthorized_release = _scenario(
        substitution_report,
        "negative-unauthorized-release",
    )
    unauthorized_return = _scenario(
        return_report,
        "negative-unauthorized-return",
    )

    failures = []
    substitution_workflow = unauthorized_release["workflow"]
    return_workflow = unauthorized_return["workflow"]

    if substitution_workflow is None:
        failures.append("substitution unauthorized-release workflow evidence is missing")
    else:
        if substitution_workflow["substitutionState"] != "PendingSettlement":
            failures.append("substitution unauthorized-release state did not stop at PendingSettlement")
        if sorted(substitution_workflow["activeEncumberedLotIds"]) != sorted(
            unauthorized_release["currentPostedLotIds"]
        ):
            failures.append("substitution unauthorized-release mutated the active encumbrance set")
        if sorted(_workflow_control_check_ids(substitution_workflow)) != [
            "APPROVAL_GATE_BLOCKED",
            "UNAUTHORIZED_RELEASE_BLOCKED",
        ]:
            failures.append("substitution unauthorized-release control checks drifted")
        if substitution_workflow["executionReportCount"] != 0:
            failures.append("substitution unauthorized-release emitted an execution report")

    if return_workflow is None:
        failures.append("return unauthorized workflow evidence is missing")
    else:
        if return_workflow["returnState"] != "PendingSettlement":
            failures.append("return unauthorized-release state did not stop at PendingSettlement")
        if sorted(return_workflow["remainingEncumberedLotIds"]) != sorted(
            unauthorized_return["currentPostedLotIds"]
        ):
            failures.append("return unauthorized-release mutated the remaining encumbrance set")
        if sorted(_workflow_control_check_ids(return_workflow)) != [
            "APPROVAL_GATE_BLOCKED",
            "UNAUTHORIZED_RETURN_BLOCKED",
        ]:
            failures.append("return unauthorized-release control checks drifted")
        if return_workflow["executionReportCount"] != 0:
            failures.append("return unauthorized-release emitted an execution report")

    return _check_result(
        check_id="AUTHORIZATION_AND_ROLE_CONTROL",
        invariant_ids=["AUTH-001", "CTRL-001", "WF-001"],
        evidence=[
            unauthorized_release["workflowResultPath"],
            unauthorized_return["workflowResultPath"],
        ],
        failures=failures,
        success_detail=(
            "Unauthorized substitution release and return release attempts were blocked by approval and role controls without changing the incumbent encumbrance set."
        ),
    )


def _check_eligibility_determinism(
    *,
    determinism_artifact: dict[str, Any],
) -> dict[str, Any]:
    failures = []
    if not determinism_artifact["matchesRepeatEvaluation"]:
        failures.append("repeated policy evaluation produced non-identical reports")

    first_report = determinism_artifact["firstReport"]
    if first_report["reportType"] != "PolicyEvaluationReport":
        failures.append("determinism artifact is not a policy evaluation report")
    if first_report["inventory"]["candidateLotCount"] <= 0:
        failures.append("determinism artifact has no candidate lots")

    return _check_result(
        check_id="ELIGIBILITY_DETERMINISM",
        invariant_ids=["ELIG-001", "PDR-001"],
        evidence=[determinism_artifact["artifactPath"]],
        failures=failures,
        success_detail=(
            "Running the same policy and inventory inputs twice produced byte-equivalent deterministic policy evaluation output."
        ),
    )


def _check_haircut_correctness(
    *,
    haircut_artifact: dict[str, Any],
) -> dict[str, Any]:
    failures = []
    asset = haircut_artifact["asset"]

    if asset["baseHaircutBps"] != haircut_artifact["expectedBaseHaircutBps"]:
        failures.append("base haircut basis points drifted from the expected schedule")
    if asset["totalHaircutBps"] != haircut_artifact["expectedTotalHaircutBps"]:
        failures.append("total haircut basis points drifted from the expected schedule")
    if asset["valuationBasisValue"] != haircut_artifact["expectedValuationBasisValue"]:
        failures.append("valuation basis value drifted from the expected market-value basis")
    if asset["lendableValue"] != haircut_artifact["expectedLendableValue"]:
        failures.append("lendable value drifted from the expected haircut-adjusted amount")

    computed_lendable = round(
        asset["valuationBasisValue"] * (1 - asset["totalHaircutBps"] / 10000),
        2,
    )
    if asset["lendableValue"] != computed_lendable:
        failures.append("reported lendable value no longer equals valuation basis times the haircut ratio")

    return _check_result(
        check_id="HAIRCUT_CORRECTNESS",
        invariant_ids=["HAIR-001"],
        evidence=[haircut_artifact["artifactPath"]],
        failures=failures,
        success_detail=(
            "The conformance haircut vector preserved the expected valuation basis, haircut schedule, and lendable-value arithmetic without hidden adjustments."
        ),
    )


def _check_no_double_encumbrance(
    *,
    margin_call_report: dict[str, Any],
    substitution_report: dict[str, Any],
    return_report: dict[str, Any],
) -> dict[str, Any]:
    failures = []

    margin_positive = _positive_scenario(margin_call_report)
    substitution_positive = _positive_scenario(substitution_report)
    substitution_blocked = _scenario(substitution_report, "negative-unauthorized-release")
    return_positive = _positive_scenario(return_report)
    return_blocked = _scenario(return_report, "negative-unauthorized-return")

    margin_workflow = margin_positive["workflow"]
    substitution_workflow = substitution_positive["workflow"]
    substitution_blocked_workflow = substitution_blocked["workflow"]
    return_workflow = return_positive["workflow"]
    return_blocked_workflow = return_blocked["workflow"]

    if margin_workflow is None:
        failures.append("margin-call workflow evidence is missing")
    else:
        if len(margin_workflow["encumberedLotIds"]) != len(
            set(margin_workflow["encumberedLotIds"])
        ):
            failures.append("margin-call workflow encumbered the same lot more than once")
        if sorted(margin_workflow["encumberedLotIds"]) != sorted(
            margin_positive["selectedLotIds"]
        ):
            failures.append("margin-call encumbered lots drifted from the optimizer-selected set")

    if substitution_workflow is None:
        failures.append("substitution workflow evidence is missing")
    else:
        active_set = set(substitution_workflow["activeEncumberedLotIds"])
        released_set = set(substitution_workflow["releasedLotIds"])
        if active_set & released_set:
            failures.append("substitution workflow reused a lot in both active and released encumbrance sets")
        if len(substitution_workflow["activeEncumberedLotIds"]) != len(active_set):
            failures.append("substitution workflow duplicated an active encumbered lot")
        if len(substitution_workflow["releasedLotIds"]) != len(released_set):
            failures.append("substitution workflow duplicated a released lot")

    if substitution_blocked_workflow is None:
        failures.append("blocked substitution workflow evidence is missing")
    else:
        if sorted(substitution_blocked_workflow["activeEncumberedLotIds"]) != sorted(
            substitution_blocked["currentPostedLotIds"]
        ):
            failures.append("blocked substitution mutated the current encumbrance set")

    if return_workflow is None:
        failures.append("return workflow evidence is missing")
    else:
        current_set = set(return_workflow["currentEncumberedLotIds"])
        returned_set = set(return_workflow["returnedLotIds"])
        remaining_set = set(return_workflow["remainingEncumberedLotIds"])
        if returned_set & remaining_set:
            failures.append("return workflow reused a lot in both returned and remaining encumbrance sets")
        if returned_set | remaining_set != current_set:
            failures.append("return workflow did not preserve the full current encumbrance universe")

    if return_blocked_workflow is None:
        failures.append("blocked return workflow evidence is missing")
    else:
        if sorted(return_blocked_workflow["remainingEncumberedLotIds"]) != sorted(
            return_blocked["currentPostedLotIds"]
        ):
            failures.append("blocked return mutated the incumbent encumbrance set")

    return _check_result(
        check_id="NO_DOUBLE_ENCUMBRANCE",
        invariant_ids=["ENC-001", "CTRL-001"],
        evidence=[
            margin_positive["workflowResultPath"],
            substitution_positive["workflowResultPath"],
            substitution_blocked["workflowResultPath"],
            return_positive["workflowResultPath"],
            return_blocked["workflowResultPath"],
        ],
        failures=failures,
        success_detail=(
            "Across posting, substitution, and return flows the suite preserved disjoint encumbrance sets and blocked state changes that would overlap or duplicate collateral commitments."
        ),
    )


def _check_atomic_substitution_when_required(
    *,
    substitution_report: dict[str, Any],
) -> dict[str, Any]:
    failures = []

    positive = _positive_scenario(substitution_report)
    partial = _scenario(substitution_report, "negative-partial-substitution")
    unauthorized = _scenario(substitution_report, "negative-unauthorized-release")

    positive_workflow = positive["workflow"]
    partial_workflow = partial["workflow"]
    unauthorized_workflow = unauthorized["workflow"]

    if positive_workflow is None:
        failures.append("positive substitution workflow evidence is missing")
    else:
        if positive_workflow["atomicityOutcome"] != "COMMITTED_ATOMICALLY":
            failures.append("positive substitution did not commit atomically")

    if partial_workflow is None:
        failures.append("partial-substitution workflow evidence is missing")
    else:
        if partial_workflow["atomicityOutcome"] != "BLOCKED_ATOMICALLY":
            failures.append("partial substitution did not fail atomically")
        if partial_workflow["releasedLotIds"]:
            failures.append("partial substitution released collateral despite being blocked")
        if sorted(partial_workflow["activeEncumberedLotIds"]) != sorted(
            partial["currentPostedLotIds"]
        ):
            failures.append("partial substitution changed the incumbent encumbrance set")
        if "PARTIAL_SUBSTITUTION_BLOCKED" not in _workflow_control_check_ids(
            partial_workflow
        ):
            failures.append("partial substitution missing explicit control evidence")

    if unauthorized_workflow is None:
        failures.append("unauthorized substitution workflow evidence is missing")
    else:
        if unauthorized_workflow["atomicityOutcome"] != "BLOCKED_ATOMICALLY":
            failures.append("unauthorized substitution did not remain blocked atomically")

    return _check_result(
        check_id="ATOMIC_SUBSTITUTION_WHEN_REQUIRED",
        invariant_ids=["ATOM-001", "CTRL-001"],
        evidence=[
            positive["workflowResultPath"],
            partial["workflowResultPath"],
            unauthorized["workflowResultPath"],
        ],
        failures=failures,
        success_detail=(
            "When full replacement is required, substitution either commits the new set atomically or leaves the incumbent encumbrances untouched."
        ),
    )


def _check_replay_safety(
    *,
    return_report: dict[str, Any],
) -> dict[str, Any]:
    replay = _scenario(return_report, "negative-replayed-return-instruction")
    workflow = replay["workflow"]
    failures = []

    if workflow is None:
        failures.append("replay workflow evidence is missing")
    else:
        if workflow["returnState"] != "Closed":
            failures.append("replay scenario did not preserve the committed original return state")
        if "REPLAY_RETURN_BLOCKED" not in _workflow_control_check_ids(workflow):
            failures.append("replay scenario did not emit a replay-blocking control check")
        if workflow["executionReportCount"] < 1:
            failures.append("replay scenario did not preserve evidence of the committed original return")
        if not workflow.get("returnRequestId"):
            failures.append("replay scenario did not preserve the replay-safe return request identifier")

    return _check_result(
        check_id="REPLAY_SAFETY",
        invariant_ids=["REPL-001"],
        evidence=[replay["workflowResultPath"]],
        failures=failures,
        success_detail=(
            "The return workflow committed the original release once and then blocked a replayed instruction using the same request identifier."
        ),
    )


def _check_report_fidelity(
    *,
    demo_reports: list[dict[str, Any]],
    repo_root: Path,
) -> dict[str, Any]:
    failures = []
    evidence = []

    for report in demo_reports:
        report_artifact_paths = [
            path
            for path in report["artifacts"].values()
            if path is not None
        ]
        evidence.extend(report_artifact_paths)

        expected_scenario_count = len(report["scenarios"])
        if report["demo"]["scenarioCount"] != expected_scenario_count:
            failures.append(f"{report['reportType']} scenarioCount drifted from the scenario list")

        positive_count = sum(1 for scenario in report["scenarios"] if scenario["mode"] == "POSITIVE")
        negative_count = sum(1 for scenario in report["scenarios"] if scenario["mode"] == "NEGATIVE")
        if report["demo"]["positiveScenarioCount"] != positive_count:
            failures.append(f"{report['reportType']} positiveScenarioCount drifted from the scenario list")
        if report["demo"]["negativeScenarioCount"] != negative_count:
            failures.append(f"{report['reportType']} negativeScenarioCount drifted from the scenario list")

        if any(check["status"] != "PASS" for check in report["invariantChecks"]):
            failures.append(f"{report['reportType']} contains a non-passing invariant check")

        for artifact_path in report_artifact_paths:
            if not (repo_root / artifact_path).is_file():
                failures.append(f"{report['reportType']} references a missing artifact {artifact_path}")

        for scenario in report["scenarios"]:
            for field in (
                "policyEvaluationReportPath",
                "optimizationReportPath",
                "workflowInputPath",
                "workflowResultPath",
            ):
                artifact_path = scenario[field]
                if artifact_path is not None and not (repo_root / artifact_path).is_file():
                    failures.append(
                        f"{report['reportType']} scenario {scenario['scenarioId']} references a missing {field}"
                    )

            workflow = scenario["workflow"]
            if workflow is not None and "executionReportCount" in workflow:
                if workflow["executionReportCount"] != len(workflow["executionReports"]):
                    failures.append(
                        f"{report['reportType']} scenario {scenario['scenarioId']} drifted between executionReportCount and executionReports"
                    )

    return _check_result(
        check_id="REPORT_FIDELITY",
        invariant_ids=["REPT-001", "PDR-001"],
        evidence=sorted(set(evidence)),
        failures=failures,
        success_detail=(
            "Every demo report references real generated artifacts, preserves scenario and workflow counts, and keeps machine-readable summaries aligned with the committed evidence files."
        ),
    )


def _check_audit_trail_completeness(
    *,
    demo_reports: list[dict[str, Any]],
) -> dict[str, Any]:
    failures = []
    evidence = []

    for report in demo_reports:
        evidence.extend(
            path
            for path in report["artifacts"].values()
            if path is not None
        )
        if not report["timeline"]:
            failures.append(f"{report['reportType']} has an empty timeline")

        positive = _positive_scenario(report)
        workflow = positive["workflow"]
        if workflow is None:
            failures.append(f"{report['reportType']} positive scenario is missing workflow evidence")
            continue

        if not workflow["steps"]:
            failures.append(f"{report['reportType']} positive workflow has no step-level audit trail")
        else:
            for step in workflow["steps"]:
                for field in ("actor", "phase", "state", "detail"):
                    if not step.get(field):
                        failures.append(
                            f"{report['reportType']} positive workflow step {step.get('step')} is missing {field}"
                        )

        if not workflow["executionReports"]:
            failures.append(f"{report['reportType']} positive workflow has no execution-report evidence")
        else:
            for execution_report in workflow["executionReports"]:
                if not execution_report.get("reportId"):
                    failures.append(f"{report['reportType']} execution report is missing reportId")
                if not execution_report.get("workflowType"):
                    failures.append(f"{report['reportType']} execution report is missing workflowType")
                if not execution_report.get("outcome"):
                    failures.append(f"{report['reportType']} execution report is missing outcome")
                if not execution_report.get("eventIds"):
                    failures.append(f"{report['reportType']} execution report is missing eventIds")
                if not execution_report.get("summary"):
                    failures.append(f"{report['reportType']} execution report is missing summary")

        workflow_timeline_entries = [
            event
            for event in report["timeline"]
            if event["scenarioId"] == positive["scenarioId"] and event["phase"] == "WORKFLOW"
        ]
        if not workflow_timeline_entries:
            failures.append(f"{report['reportType']} positive scenario has no workflow timeline entry")

    return _check_result(
        check_id="AUDIT_TRAIL_COMPLETENESS",
        invariant_ids=["AUD-001"],
        evidence=sorted(set(evidence)),
        failures=failures,
        success_detail=(
            "Each positive flow records step-level workflow history, execution-report events, and top-level timeline entries that can be audited without hidden reconstruction."
        ),
    )


def _render_conformance_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Conformance Suite Summary",
        "",
        f"- Suite ID: `{report['suiteId']}`",
        f"- Command: `{report['command']}`",
        f"- Overall status: `{report['overallStatus']}`",
        f"- Scenario coverage: `{report['coverage']['totalScenarioCount']}` total / `{report['coverage']['positiveScenarioCount']}` positive / `{report['coverage']['negativeScenarioCount']}` negative",
        "",
        "## Checks",
        "",
        "| Check | Status | Invariants | Evidence | Detail |",
        "| --- | --- | --- | --- | --- |",
    ]

    for check in report["checks"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    check["checkId"],
                    check["status"],
                    ", ".join(f"`{item}`" for item in check["invariantIds"]),
                    ", ".join(f"`{item}`" for item in check["evidence"]),
                    check["detail"],
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Demo Reports",
            "",
            "| Demo | Report Type | Positive | Negative | Report |",
            "| --- | --- | --- | --- | --- |",
        ]
    )

    for demo_report in report["demoReports"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    demo_report["demoType"],
                    demo_report["reportType"],
                    ", ".join(demo_report["positiveScenarioIds"]),
                    ", ".join(demo_report["negativeScenarioIds"]),
                    f"`{demo_report['reportPath']}`",
                ]
            )
            + " |"
        )

    return "\n".join(lines) + "\n"


def _demo_report_entry(
    *,
    demo_type: str,
    report_type: str,
    report: dict[str, Any],
    report_path_key: str,
) -> dict[str, Any]:
    return {
        "demoType": demo_type,
        "reportType": report_type,
        "command": report["demo"]["command"],
        "reportPath": report["artifacts"][report_path_key],
        "summaryPath": report["artifacts"]["markdownSummaryPath"],
        "timelinePath": report["artifacts"]["timelinePath"],
        "positiveScenarioIds": [
            scenario["scenarioId"] for scenario in report["scenarios"] if scenario["mode"] == "POSITIVE"
        ],
        "negativeScenarioIds": [
            scenario["scenarioId"] for scenario in report["scenarios"] if scenario["mode"] == "NEGATIVE"
        ],
    }


def _scenario(report: dict[str, Any], scenario_id: str) -> dict[str, Any]:
    for scenario in report["scenarios"]:
        if scenario["scenarioId"] == scenario_id:
            return scenario
    raise DemoExecutionError(f"Missing conformance scenario {scenario_id}")


def _positive_scenario(report: dict[str, Any]) -> dict[str, Any]:
    for scenario in report["scenarios"]:
        if scenario["mode"] == "POSITIVE":
            return scenario
    raise DemoExecutionError(f"{report['reportType']} has no positive scenario")


def _workflow_control_check_ids(workflow: dict[str, Any]) -> list[str]:
    return sorted(check["checkId"] for check in workflow.get("controlChecks", []))


def _asset_result(report: dict[str, Any], lot_id: str) -> dict[str, Any]:
    for asset in report["assetResults"]:
        if asset["lotId"] == lot_id:
            return asset
    raise DemoExecutionError(f"Missing policy-evaluation result for lot {lot_id}")


def _relaxed_policy(policy: dict[str, Any]) -> dict[str, Any]:
    relaxed = copy.deepcopy(policy)
    for limit in relaxed["concentrationLimits"]:
        if limit["threshold"]["metric"] == "ABSOLUTE_MARKET_VALUE":
            limit["threshold"]["value"] = 10**12
        else:
            limit["threshold"]["value"] = 1
    return relaxed


def _check_result(
    *,
    check_id: str,
    invariant_ids: list[str],
    evidence: list[str],
    failures: list[str],
    success_detail: str,
) -> dict[str, Any]:
    status = "PASS" if not failures else "FAIL"
    detail = success_detail if status == "PASS" else "; ".join(failures) + "."
    return {
        "checkId": check_id,
        "status": status,
        "invariantIds": invariant_ids,
        "evidence": [item for item in evidence if item is not None],
        "detail": detail,
    }


def _suite_id(
    *,
    checks: list[dict[str, Any]],
    demo_reports: list[dict[str, Any]],
    determinism_artifact: dict[str, Any],
    haircut_artifact: dict[str, Any],
) -> str:
    canonical = json.dumps(
        {
            "checks": checks,
            "demoIds": [report["demo"]["demoId"] for report in demo_reports],
            "determinismEvaluationId": determinism_artifact["firstReport"]["evaluationId"],
            "haircutEvaluationId": haircut_artifact["report"]["evaluationId"],
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"csr-{digest[:16]}"


def _resolve_path(repo_root: Path, candidate: str | Path) -> Path:
    candidate_path = Path(candidate)
    if candidate_path.is_absolute():
        return candidate_path
    return (repo_root / candidate_path).resolve()
