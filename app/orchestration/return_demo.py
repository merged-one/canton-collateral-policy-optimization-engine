"""End-to-end collateral return demo orchestration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from margin_call_demo import (
    DemoExecutionError,
    _append_timeline,
    _assert_equal,
    _assert_reason_codes,
    _load_json,
    _optimization_reason_codes as _base_optimization_reason_codes,
    _policy_reason_codes,
    _relative_path,
    _resolve_scenario_path,
    _run_daml_workflow,
    _utc_now,
    _validate_json_schema,
    _write_json,
    _write_text,
    evaluate_policy,
    optimize_collateral,
    write_optimization_report,
    write_policy_report,
)


def run_return_demo(
    *,
    manifest_path: str | Path,
    output_dir: str | Path,
    repo_root: str | Path,
) -> dict[str, Any]:
    repo_root_path = Path(repo_root).resolve()
    manifest = _load_json(manifest_path)
    manifest_path_obj = Path(manifest_path).resolve()
    output_dir_path = Path(output_dir).resolve()
    output_dir_path.mkdir(parents=True, exist_ok=True)

    timeline: list[dict[str, Any]] = []
    scenario_results: list[dict[str, Any]] = []

    for sequence, scenario in enumerate(manifest["scenarios"], start=1):
        scenario_results.append(
            _run_scenario(
                scenario=scenario,
                sequence=sequence,
                manifest_path=manifest_path_obj,
                output_dir=output_dir_path,
                repo_root=repo_root_path,
                timeline=timeline,
            )
        )

    invariant_checks = _build_invariant_checks(scenario_results)
    return_report = _build_return_report(
        manifest=manifest,
        manifest_path=manifest_path_obj,
        repo_root=repo_root_path,
        output_dir=output_dir_path,
        scenario_results=scenario_results,
        timeline=timeline,
        invariant_checks=invariant_checks,
    )

    report_path = output_dir_path / "return-demo-report.json"
    summary_path = output_dir_path / "return-demo-summary.md"
    timeline_path = output_dir_path / "return-demo-timeline.md"

    return_report["artifacts"] = {
        "returnReportPath": _relative_path(report_path, repo_root_path),
        "markdownSummaryPath": _relative_path(summary_path, repo_root_path),
        "timelinePath": _relative_path(timeline_path, repo_root_path),
    }

    _write_json(report_path, return_report)
    _validate_json_schema(
        report_path=report_path,
        schema_path=repo_root_path / "reports/schemas/return-report.schema.json",
    )

    _write_markdown_summary(summary_path, return_report)
    _write_timeline_markdown(timeline_path, return_report)

    return return_report


def _run_scenario(
    *,
    scenario: dict[str, Any],
    sequence: int,
    manifest_path: Path,
    output_dir: Path,
    repo_root: Path,
    timeline: list[dict[str, Any]],
) -> dict[str, Any]:
    scenario_id = scenario["scenarioId"]
    scenario_mode = scenario["mode"]
    expected = scenario["expected"]
    resolved_policy_path = _resolve_scenario_path(manifest_path, scenario["policy"])
    resolved_inventory_path = _resolve_scenario_path(manifest_path, scenario["inventory"])
    resolved_obligation_path = (
        _resolve_scenario_path(manifest_path, scenario["obligation"])
        if scenario.get("obligation")
        else None
    )

    policy = _load_json(resolved_policy_path)
    inventory = _load_json(resolved_inventory_path)
    obligation = _load_json(resolved_obligation_path) if resolved_obligation_path else None

    policy_report_path = output_dir / f"{scenario_id}-policy-evaluation-report.json"
    optimization_report_path = (
        output_dir / f"{scenario_id}-optimization-report.json"
        if scenario.get("runOptimization", False)
        else None
    )
    workflow_input_path = (
        output_dir / f"{scenario_id}-workflow-input.json"
        if scenario.get("runWorkflow", False)
        else None
    )
    workflow_result_path = (
        output_dir / f"{scenario_id}-workflow-result.json"
        if scenario.get("runWorkflow", False)
        else None
    )

    policy_started_at = _utc_now()
    policy_report = evaluate_policy(policy, inventory)
    write_policy_report(policy_report, policy_report_path)
    _validate_json_schema(
        report_path=policy_report_path,
        schema_path=repo_root / "reports/schemas/policy-evaluation-report.schema.json",
    )
    policy_finished_at = _utc_now()
    _append_timeline(
        timeline=timeline,
        sequence=sequence,
        scenario_id=scenario_id,
        phase="POLICY_EVALUATION",
        status="COMPLETED",
        started_at=policy_started_at,
        finished_at=policy_finished_at,
        artifact_path=_relative_path(policy_report_path, repo_root),
        detail=(
            f"Evaluated currently encumbered collateral for {scenario_mode.lower()} scenario "
            f"with overall decision {policy_report['overallDecision']}."
        ),
    )
    _assert_equal(
        actual=policy_report["overallDecision"],
        expected=expected["policyOverallDecision"],
        message=f"{scenario_id}: unexpected policy overall decision",
    )

    optimization_report = None
    if scenario.get("runOptimization", False):
        if obligation is None or optimization_report_path is None:
            raise DemoExecutionError(
                f"{scenario_id}: optimization requested without an obligation input"
            )
        optimization_started_at = _utc_now()
        optimization_report = optimize_collateral(policy, inventory, obligation)
        write_optimization_report(optimization_report, optimization_report_path)
        _validate_json_schema(
            report_path=optimization_report_path,
            schema_path=repo_root / "reports/schemas/optimization-report.schema.json",
        )
        optimization_finished_at = _utc_now()
        _append_timeline(
            timeline=timeline,
            sequence=sequence,
            scenario_id=scenario_id,
            phase="OPTIMIZATION",
            status="COMPLETED",
            started_at=optimization_started_at,
            finished_at=optimization_finished_at,
            artifact_path=_relative_path(optimization_report_path, repo_root),
            detail=(
                f"Optimized the retained encumbered set for scenario {scenario_id} with "
                f"optimizer action {optimization_report['recommendedAction']}."
            ),
        )
        _assert_equal(
            actual=optimization_report["status"],
            expected=expected["optimizationStatus"],
            message=f"{scenario_id}: unexpected optimization status",
        )

    workflow_request = None
    workflow_result = None
    if scenario.get("runWorkflow", False):
        if optimization_report is None or obligation is None:
            raise DemoExecutionError(
                f"{scenario_id}: workflow requested without optimization output"
            )
        if workflow_input_path is None or workflow_result_path is None:
            raise DemoExecutionError(f"{scenario_id}: workflow artifact paths are missing")
        workflow_request = _build_workflow_request(
            scenario=scenario,
            inventory=inventory,
            obligation=obligation,
            policy=policy,
            policy_report=policy_report,
            optimization_report=optimization_report,
        )
        _write_json(workflow_input_path, workflow_request)
        workflow_started_at = _utc_now()
        workflow_result = _run_daml_workflow(
            script_name=scenario["workflow"]["scriptName"],
            input_path=workflow_input_path,
            output_path=workflow_result_path,
            repo_root=repo_root,
        )
        workflow_finished_at = _utc_now()
        _append_timeline(
            timeline=timeline,
            sequence=sequence,
            scenario_id=scenario_id,
            phase="WORKFLOW",
            status="COMPLETED",
            started_at=workflow_started_at,
            finished_at=workflow_finished_at,
            artifact_path=_relative_path(workflow_result_path, repo_root),
            detail=_workflow_timeline_detail(scenario_id, workflow_result),
        )
        _validate_workflow_result(
            scenario_id=scenario_id,
            workflow_result=workflow_result,
            expected=expected,
        )

    observed_reason_codes = sorted(
        set(_policy_reason_codes(policy_report))
        | set(_return_optimization_reason_codes(optimization_report))
        | set(_workflow_reason_codes(workflow_result, scenario_mode=scenario_mode))
    )
    _assert_reason_codes(
        scenario_id=scenario_id,
        observed_reason_codes=observed_reason_codes,
        expected_reason_codes=expected.get("reasonCodes", []),
    )

    retained_lot_ids, return_lot_ids = _retained_and_returned_lot_ids(
        optimization_report=optimization_report,
        workflow_request=workflow_request,
    )
    requested_return_quantity = (
        None
        if workflow_request is None
        else round(sum(lot["quantity"] for lot in workflow_request["returnLots"]), 2)
    )
    remaining_required_coverage = (
        None if workflow_request is None else workflow_request["remainingRequiredCoverage"]
    )

    return {
        "scenarioId": scenario_id,
        "mode": scenario_mode,
        "description": scenario["description"],
        "result": "SUCCESS" if scenario_mode == "POSITIVE" else "EXPECTED_FAILURE",
        "summary": _scenario_summary(
            scenario=scenario,
            optimization_report=optimization_report,
            workflow_result=workflow_result,
            retained_lot_ids=retained_lot_ids,
            return_lot_ids=return_lot_ids,
        ),
        "observedReasonCodes": observed_reason_codes,
        "expectedReasonCodes": expected.get("reasonCodes", []),
        "policyEvaluationReportPath": _relative_path(policy_report_path, repo_root),
        "optimizationReportPath": (
            None
            if optimization_report_path is None
            else _relative_path(optimization_report_path, repo_root)
        ),
        "workflowInputPath": (
            None if workflow_input_path is None else _relative_path(workflow_input_path, repo_root)
        ),
        "workflowResultPath": (
            None
            if workflow_result_path is None
            else _relative_path(workflow_result_path, repo_root)
        ),
        "policyDecision": policy_report["overallDecision"],
        "optimizationStatus": (
            None if optimization_report is None else optimization_report["status"]
        ),
        "currentPostedLotIds": [] if obligation is None else obligation["currentPostedLotIds"],
        "retainedLotIds": retained_lot_ids,
        "returnLotIds": return_lot_ids,
        "requestedReturnQuantity": requested_return_quantity,
        "remainingRequiredCoverage": remaining_required_coverage,
        "workflow": workflow_result,
    }


def _build_workflow_request(
    *,
    scenario: dict[str, Any],
    inventory: dict[str, Any],
    obligation: dict[str, Any],
    policy: dict[str, Any],
    policy_report: dict[str, Any],
    optimization_report: dict[str, Any],
) -> dict[str, Any]:
    recommended_portfolio = optimization_report["recommendedPortfolio"]
    recommendation = optimization_report["substitutionRecommendation"]
    if recommended_portfolio is None or recommendation is None:
        raise DemoExecutionError(
            f"{scenario['scenarioId']}: workflow requested without a retained-set recommendation"
        )

    inventory_by_lot_id = {lot["lotId"]: lot for lot in inventory["candidateLots"]}
    workflow_config = scenario["workflow"]
    current_posted_lot_ids = obligation["currentPostedLotIds"]
    return_lot_ids = recommendation["removeLotIds"]
    if not return_lot_ids:
        raise DemoExecutionError(
            f"{scenario['scenarioId']}: optimizer did not select any lots for return"
        )

    current_posted_lots = [
        _workflow_lot_input(
            lot=inventory_by_lot_id[lot_id],
            workflow_config=workflow_config,
            source_account=workflow_config["sourceAccount"],
            destination_account=workflow_config["destinationAccount"],
        )
        for lot_id in current_posted_lot_ids
    ]
    return_lots = [
        _workflow_lot_input(
            lot=inventory_by_lot_id[lot_id],
            workflow_config=workflow_config,
            source_account=workflow_config["sourceAccount"],
            destination_account=workflow_config["destinationAccount"],
        )
        for lot_id in return_lot_ids
    ]

    current_secured_amount = round(
        sum(lot["quantity"] for lot in current_posted_lots),
        2,
    )
    remaining_required_coverage = workflow_config.get(
        "remainingRequiredCoverageOverride", obligation["obligationAmount"]
    )

    return {
        "scenarioId": scenario["scenarioId"],
        "obligationId": obligation["obligationId"],
        "returnRequestId": workflow_config.get(
            "returnRequestId", f"{workflow_config['correlationId']}-return"
        ),
        "correlationId": workflow_config["correlationId"],
        "policyVersion": policy["policyVersion"],
        "snapshotId": workflow_config.get(
            "snapshotId",
            f"{inventory['inventorySetId']}::{inventory['evaluationContext']['asOf']}",
        ),
        "decisionReference": workflow_config.get(
            "decisionReference", policy_report["evaluationId"]
        ),
        "currentSecuredAmount": current_secured_amount,
        "remainingRequiredCoverage": remaining_required_coverage,
        "currentPostedLots": current_posted_lots,
        "returnLots": return_lots,
        "requiresSecuredPartyApproval": workflow_config.get(
            "requiresSecuredPartyApproval", True
        ),
        "requiresCustodianApproval": workflow_config.get(
            "requiresCustodianApproval", True
        ),
        "simulateUnauthorizedReleaseAttempt": workflow_config.get(
            "simulateUnauthorizedReleaseAttempt", False
        ),
        "simulateReplayAttempt": workflow_config.get("simulateReplayAttempt", False),
    }


def _workflow_lot_input(
    *,
    lot: dict[str, Any],
    workflow_config: dict[str, Any],
    source_account: str,
    destination_account: str,
) -> dict[str, Any]:
    quantity = _lot_quantity(lot)
    return {
        "lotId": lot["lotId"],
        "assetId": lot["assetId"],
        "issuer": lot["issuerId"],
        "assetClass": lot["assetClass"],
        "currency": lot["currency"],
        "settlementSystem": workflow_config["settlementSystem"],
        "tokenAdapterReference": workflow_config.get(
            "tokenAdapterReferencePrefix", "demo/adapter"
        )
        + f"/{lot['assetId']}",
        "jurisdiction": lot["issuanceJurisdiction"],
        "transferabilityFlags": workflow_config.get(
            "transferabilityFlags",
            ["deliverable", "pledgeable", "segregated"],
        ),
        "custodyAccount": workflow_config["custodyAccount"],
        "quantity": quantity,
        "sourceAccount": source_account,
        "destinationAccount": destination_account,
    }


def _lot_quantity(lot: dict[str, Any]) -> float:
    quantity = lot.get("nominalValue", lot.get("marketValue"))
    if quantity is None:
        raise DemoExecutionError(
            f"lot {lot['lotId']} lacks nominalValue and marketValue for workflow input"
        )
    return quantity


def _validate_workflow_result(
    *,
    scenario_id: str,
    workflow_result: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    _assert_equal(
        actual=workflow_result["returnState"],
        expected=expected["workflowReturnState"],
        message=f"{scenario_id}: unexpected return workflow state",
    )
    _assert_equal(
        actual=sorted(workflow_result["currentEncumberedLotIds"]),
        expected=sorted(expected["currentEncumberedLotIds"]),
        message=f"{scenario_id}: current encumbered lot set drifted from expectation",
    )
    _assert_equal(
        actual=sorted(workflow_result["returnedLotIds"]),
        expected=sorted(expected["returnedLotIds"]),
        message=f"{scenario_id}: returned lot set drifted from expectation",
    )
    _assert_equal(
        actual=sorted(workflow_result["remainingEncumberedLotIds"]),
        expected=sorted(expected["remainingEncumberedLotIds"]),
        message=f"{scenario_id}: remaining encumbered set drifted from expectation",
    )
    _assert_equal(
        actual=workflow_result["releaseConditionSatisfied"],
        expected=expected["releaseConditionSatisfied"],
        message=f"{scenario_id}: release-condition result drifted from expectation",
    )
    _assert_equal(
        actual=workflow_result["atomicityOutcome"],
        expected=expected["atomicityOutcome"],
        message=f"{scenario_id}: atomicity outcome drifted from expectation",
    )
    if "requiredControlChecks" in expected:
        _assert_equal(
            actual=sorted(check["checkId"] for check in workflow_result["controlChecks"]),
            expected=sorted(expected["requiredControlChecks"]),
            message=f"{scenario_id}: workflow control checks drifted from expectation",
        )
    if workflow_result["executionReportCount"] < expected["minimumExecutionReportCount"]:
        raise DemoExecutionError(
            f"{scenario_id}: expected at least {expected['minimumExecutionReportCount']} "
            f"execution reports but found {workflow_result['executionReportCount']}"
        )


def _workflow_reason_codes(
    workflow_result: dict[str, Any] | None,
    *,
    scenario_mode: str,
) -> list[str]:
    if workflow_result is None or scenario_mode != "NEGATIVE":
        return []
    return sorted(check["checkId"] for check in workflow_result["controlChecks"])


def _return_optimization_reason_codes(
    optimization_report: dict[str, Any] | None,
) -> list[str]:
    if optimization_report is None:
        return []
    decision_trace = next(
        (
            trace
            for trace in optimization_report["explanationTrace"]
            if trace["stage"] == "DECISION" and trace["reasonCodes"]
        ),
        None,
    )
    if decision_trace is not None:
        return sorted(set(decision_trace["reasonCodes"]))
    return _base_optimization_reason_codes(optimization_report)


def _workflow_timeline_detail(
    scenario_id: str,
    workflow_result: dict[str, Any],
) -> str:
    control_check_ids = {check["checkId"] for check in workflow_result["controlChecks"]}
    if workflow_result["returnState"] == "Closed":
        if "REPLAY_RETURN_BLOCKED" in control_check_ids:
            return (
                f"Recorded the Daml return workflow for scenario {scenario_id}, "
                "settled the original return, and blocked a replayed instruction."
            )
        return (
            f"Recorded the Daml return workflow for scenario {scenario_id} and "
            "confirmed settlement-driven encumbrance release."
        )
    return (
        f"Recorded the Daml return control failure for scenario {scenario_id} "
        f"with workflow state {workflow_result['returnState']}."
    )


def _build_return_report(
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    repo_root: Path,
    output_dir: Path,
    scenario_results: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
    invariant_checks: list[dict[str, Any]],
) -> dict[str, Any]:
    positive_scenarios = [scenario for scenario in scenario_results if scenario["mode"] == "POSITIVE"]
    negative_scenarios = [scenario for scenario in scenario_results if scenario["mode"] == "NEGATIVE"]
    canonical = json.dumps(
        {"manifest": manifest, "scenarioResults": scenario_results},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    primary_optimization_ref = (
        positive_scenarios[0]["optimizationReportPath"] if positive_scenarios else None
    )

    return {
        "$schema": "../../reports/schemas/return-report.schema.json",
        "reportType": "ReturnReport",
        "reportVersion": "0.1.0",
        "returnReportId": f"rrr-{digest[:16]}",
        "generatedAt": _utc_now(),
        "overallStatus": "PASS",
        "demo": {
            "demoId": manifest["demoId"],
            "demoVersion": manifest["demoVersion"],
            "command": "make demo-return",
            "manifestPath": _relative_path(manifest_path, repo_root),
            "outputDirectory": _relative_path(output_dir, repo_root),
            "primaryOptimizationArtifact": primary_optimization_ref,
            "scenarioCount": len(scenario_results),
            "positiveScenarioCount": len(positive_scenarios),
            "negativeScenarioCount": len(negative_scenarios),
        },
        "artifacts": {},
        "scenarios": scenario_results,
        "timeline": timeline,
        "invariantChecks": invariant_checks,
    }


def _build_invariant_checks(
    scenario_results: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    positive_scenario = next(
        scenario for scenario in scenario_results if scenario["mode"] == "POSITIVE"
    )
    replay_scenario = next(
        scenario
        for scenario in scenario_results
        if scenario["scenarioId"] == "negative-replayed-return-instruction"
    )
    negative_scenarios = [
        scenario for scenario in scenario_results if scenario["mode"] == "NEGATIVE"
    ]

    negative_workflow_evidence = [
        scenario["workflowResultPath"]
        for scenario in negative_scenarios
        if scenario["workflowResultPath"] is not None
    ]
    negative_artifact_evidence = sorted(
        {
            artifact
            for scenario in negative_scenarios
            for artifact in (
                scenario["policyEvaluationReportPath"],
                scenario["optimizationReportPath"],
                scenario["workflowResultPath"],
            )
            if artifact is not None
        }
    )

    return [
        {
            "invariantId": "PDR-001",
            "status": "PASS",
            "evidence": [positive_scenario["policyEvaluationReportPath"]],
            "note": "The positive return path used a generated policy-evaluation report derived from declared inputs.",
        },
        {
            "invariantId": "ALLOC-001",
            "status": "PASS",
            "evidence": [positive_scenario["optimizationReportPath"]],
            "note": "The optimizer selected the retained encumbered set deterministically and the returned lots were derived from that recommendation.",
        },
        {
            "invariantId": "CTRL-001",
            "status": "PASS",
            "evidence": negative_workflow_evidence,
            "note": "The return workflow blocked unauthorized release, replay, and obligation-state mismatch paths with explicit control checks instead of silently mutating encumbrance state.",
        },
        {
            "invariantId": "ATOM-001",
            "status": "PASS",
            "evidence": [
                positive_scenario["workflowResultPath"],
                *negative_workflow_evidence,
            ],
            "note": "The positive path released only the selected encumbrances, while blocked return paths preserved the incumbent encumbrance set.",
        },
        {
            "invariantId": "REPL-001",
            "status": "PASS",
            "evidence": [replay_scenario["workflowResultPath"]],
            "note": "The replayed return instruction was rejected because the active return request identifier remained reserved after the committed release.",
        },
        {
            "invariantId": "REPT-001",
            "status": "PASS",
            "evidence": [
                positive_scenario["workflowResultPath"],
                positive_scenario["policyEvaluationReportPath"],
                positive_scenario["optimizationReportPath"],
            ],
            "note": "The return report references real workflow, policy, and optimization artifacts rather than operator-authored placeholders.",
        },
        {
            "invariantId": "EXCP-001",
            "status": "PASS",
            "evidence": negative_artifact_evidence,
            "note": "The negative return scenarios failed deterministically for unauthorized release, replayed return instruction, and obligation-state mismatch conditions.",
        },
    ]


def _retained_and_returned_lot_ids(
    *,
    optimization_report: dict[str, Any] | None,
    workflow_request: dict[str, Any] | None,
) -> tuple[list[str], list[str]]:
    if workflow_request is not None:
        retained = sorted(
            lot["lotId"]
            for lot in workflow_request["currentPostedLots"]
            if lot["lotId"] not in {item["lotId"] for item in workflow_request["returnLots"]}
        )
        returned = sorted(lot["lotId"] for lot in workflow_request["returnLots"])
        return retained, returned

    if optimization_report is None:
        return [], []

    recommendation = optimization_report["substitutionRecommendation"]
    if recommendation is None:
        return [], []
    return (
        sorted(recommendation["recommendedLotIds"]),
        sorted(recommendation["removeLotIds"]),
    )


def _scenario_summary(
    *,
    scenario: dict[str, Any],
    optimization_report: dict[str, Any] | None,
    workflow_result: dict[str, Any] | None,
    retained_lot_ids: list[str],
    return_lot_ids: list[str],
) -> str:
    if scenario["mode"] == "POSITIVE":
        assert optimization_report is not None
        assert workflow_result is not None
        return (
            f"The optimizer retained {', '.join(retained_lot_ids)}, selected "
            f"{', '.join(return_lot_ids)} for release, and the Daml workflow "
            "closed with the returned encumbrances moved to released state."
        )

    if workflow_result is None:
        return "The return scenario did not reach the Daml workflow layer."

    control_check_ids = sorted(check["checkId"] for check in workflow_result["controlChecks"])
    if workflow_result["returnState"] == "Closed":
        return (
            f"The original return settled for {', '.join(return_lot_ids)}, and the "
            f"workflow then blocked the replay path with control checks {', '.join(control_check_ids)}."
        )

    return (
        f"The workflow stayed in state {workflow_result['returnState']} and blocked the "
        f"control path with checks {', '.join(control_check_ids)}."
    )


def _write_markdown_summary(path: Path, return_report: dict[str, Any]) -> None:
    lines = [
        "# Return Demo Summary",
        "",
        "## Overview",
        "",
        f"- Return report: `{return_report['artifacts']['returnReportPath']}`",
        f"- Scenario count: `{return_report['demo']['scenarioCount']}`",
        f"- Primary optimization artifact: `{return_report['demo']['primaryOptimizationArtifact']}`",
        "",
        "## Scenario Results",
        "",
        "| Scenario | Mode | Result | Summary |",
        "| --- | --- | --- | --- |",
    ]

    for scenario in return_report["scenarios"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    scenario["scenarioId"],
                    scenario["mode"],
                    scenario["result"],
                    scenario["summary"],
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Invariant Checks",
            "",
            "| Invariant | Status | Evidence | Note |",
            "| --- | --- | --- | --- |",
        ]
    )

    for invariant in return_report["invariantChecks"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    invariant["invariantId"],
                    invariant["status"],
                    ", ".join(f"`{item}`" for item in invariant["evidence"]),
                    invariant["note"],
                ]
            )
            + " |"
        )

    positive_scenario = next(
        scenario for scenario in return_report["scenarios"] if scenario["mode"] == "POSITIVE"
    )
    lines.extend(
        [
            "",
            "## Positive Workflow Path",
            "",
            f"- Retained lots: `{', '.join(positive_scenario['retainedLotIds'])}`",
            f"- Returned lots: `{', '.join(positive_scenario['returnLotIds'])}`",
            f"- Workflow result artifact: `{positive_scenario['workflowResultPath']}`",
            "",
        ]
    )

    _write_text(path, "\n".join(lines) + "\n")


def _write_timeline_markdown(path: Path, return_report: dict[str, Any]) -> None:
    lines = [
        "# Return Demo Timeline",
        "",
        "## Execution Phases",
        "",
        "| Seq | Scenario | Phase | Status | Artifact | Detail |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for event in return_report["timeline"]:
        lines.append(
            "| "
            + " | ".join(
                [
                    str(event["sequence"]),
                    event["scenarioId"],
                    event["phase"],
                    event["status"],
                    "" if event["artifactPath"] is None else f"`{event['artifactPath']}`",
                    event["detail"],
                ]
            )
            + " |"
        )

    positive_scenario = next(
        scenario for scenario in return_report["scenarios"] if scenario["mode"] == "POSITIVE"
    )
    workflow = positive_scenario["workflow"]
    if workflow is not None:
        lines.extend(
            [
                "",
                "## Positive Workflow Steps",
                "",
                "| Step | Phase | Actor | State | Detail |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for step in workflow["steps"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(step["step"]),
                        step["phase"],
                        step["actor"],
                        step["state"],
                        step["detail"],
                    ]
                )
                + " |"
            )

    _write_text(path, "\n".join(lines) + "\n")
