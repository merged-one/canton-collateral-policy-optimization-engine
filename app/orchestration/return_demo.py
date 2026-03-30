"""End-to-end collateral return demo orchestration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from margin_call_demo import (
    ADAPTER_BLOCKED,
    ADAPTER_EXECUTED,
    ADAPTER_NOT_REQUESTED,
    BLOCKING_ADAPTER,
    BLOCKING_OPTIMIZATION,
    BLOCKING_POLICY,
    BLOCKING_WORKFLOW,
    QUICKSTART_CONTROL_PLANE_STATE_ROOT,
    RUNTIME_IDE_LEDGER,
    RUNTIME_QUICKSTART,
    DemoExecutionError,
    _append_timeline,
    _assert_equal,
    _assert_reason_codes,
    _compact_paths,
    _load_json,
    _localnet_env,
    _optimization_reason_codes as _base_optimization_reason_codes,
    _policy_reason_codes,
    _relative_path,
    _resolve_scenario_path,
    _run_command,
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
    runtime_mode: str = RUNTIME_IDE_LEDGER,
    report_basename: str | None = None,
    command_name: str | None = None,
) -> dict[str, Any]:
    repo_root_path = Path(repo_root).resolve()
    manifest = _load_json(manifest_path)
    manifest_path_obj = Path(manifest_path).resolve()
    output_dir_path = Path(output_dir).resolve()
    output_dir_path.mkdir(parents=True, exist_ok=True)

    normalized_runtime_mode = runtime_mode.upper()
    if normalized_runtime_mode not in {RUNTIME_IDE_LEDGER, RUNTIME_QUICKSTART}:
        raise DemoExecutionError(f"unsupported return runtime mode {runtime_mode!r}")

    report_stem = report_basename or _default_report_basename(normalized_runtime_mode)
    command = command_name or _default_command_name(normalized_runtime_mode)

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
                runtime_mode=normalized_runtime_mode,
                timeline=timeline,
            )
        )

    invariant_checks = _build_invariant_checks(
        scenario_results=scenario_results,
        runtime_mode=normalized_runtime_mode,
    )
    return_report = _build_return_report(
        manifest=manifest,
        manifest_path=manifest_path_obj,
        repo_root=repo_root_path,
        output_dir=output_dir_path,
        scenario_results=scenario_results,
        timeline=timeline,
        invariant_checks=invariant_checks,
        runtime_mode=normalized_runtime_mode,
        command_name=command,
    )

    report_path = output_dir_path / f"{report_stem}-report.json"
    summary_path = output_dir_path / f"{report_stem}-summary.md"
    timeline_path = output_dir_path / f"{report_stem}-timeline.md"

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
    runtime_mode: str,
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
    quickstart_seed_receipt_path: Path | None = None
    adapter_execution_report_path: Path | None = None
    adapter_status_path: Path | None = None

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
    adapter_report = None
    adapter_status = None

    if scenario.get("runWorkflow", False):
        if optimization_report is None or obligation is None:
            raise DemoExecutionError(
                f"{scenario_id}: workflow requested without optimization output"
            )
        if workflow_input_path is None or workflow_result_path is None:
            raise DemoExecutionError(f"{scenario_id}: workflow artifact paths are missing")

        if runtime_mode == RUNTIME_IDE_LEDGER:
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
            workflow_result = {
                "correlationId": workflow_request["correlationId"],
                "workflowGate": None,
                "settlementInstructionId": None,
                "settlementInstructionState": None,
                **workflow_result,
            }
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
                detail=_ide_workflow_timeline_detail(scenario_id, workflow_result),
            )
            _validate_ide_workflow_result(
                scenario_id=scenario_id,
                workflow_result=workflow_result,
                expected=expected,
            )
        else:
            quickstart_artifact_dir = output_dir / scenario_id
            quickstart_state_dir = QUICKSTART_CONTROL_PLANE_STATE_ROOT / scenario_id
            quickstart_artifact_dir.mkdir(parents=True, exist_ok=True)
            quickstart_state_dir.mkdir(parents=True, exist_ok=True)
            quickstart_manifest_path = _resolve_scenario_path(
                manifest_path,
                scenario["quickstartScenarioManifest"],
            )

            seed_started_at = _utc_now()
            quickstart_seed_receipt_path = _run_quickstart_seed(
                repo_root=repo_root,
                scenario_artifact_dir=quickstart_artifact_dir,
                scenario_state_dir=quickstart_state_dir,
                quickstart_manifest_path=quickstart_manifest_path,
            )
            seed_finished_at = _utc_now()
            _append_timeline(
                timeline=timeline,
                sequence=sequence,
                scenario_id=scenario_id,
                phase="QUICKSTART_SEED",
                status="COMPLETED",
                started_at=seed_started_at,
                finished_at=seed_finished_at,
                artifact_path=_relative_path(quickstart_seed_receipt_path, repo_root),
                detail=(
                    f"Seeded or reused the declared Quickstart return scenario for "
                    f"{scenario_id} before workflow execution."
                ),
            )

            seed_receipt = _load_json(quickstart_seed_receipt_path)
            workflow_request = _build_quickstart_workflow_request(
                scenario=scenario,
                obligation=obligation,
                policy=policy,
                optimization_report=optimization_report,
                seed_receipt=seed_receipt,
            )
            _write_json(workflow_input_path, workflow_request)

            workflow_started_at = _utc_now()
            workflow_result = _run_quickstart_workflow(
                repo_root=repo_root,
                scenario_artifact_dir=quickstart_artifact_dir,
                scenario_state_dir=quickstart_state_dir,
                workflow_input_path=workflow_input_path,
                workflow_result_path=workflow_result_path,
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
                detail=_quickstart_workflow_timeline_detail(scenario_id, workflow_result),
            )
            _validate_quickstart_workflow_result(
                scenario_id=scenario_id,
                workflow_result=workflow_result,
                expected=expected,
            )

            status_output_path = quickstart_artifact_dir / "localnet-return-status.json"
            if scenario.get("runAdapter", False):
                adapter_input_path = quickstart_state_dir / "return-adapter-input.json"
                adapter_execution_report_path = (
                    quickstart_artifact_dir / "localnet-return-adapter-execution-report.json"
                )
                adapter_request = _build_quickstart_adapter_input(
                    seed_receipt=seed_receipt,
                    workflow_request=workflow_request,
                    workflow_result=workflow_result,
                    simulate_replay_attempt=scenario.get("workflow", {}).get(
                        "simulateReplayAttempt", False
                    ),
                )
                _write_json(adapter_input_path, adapter_request)
                adapter_started_at = _utc_now()
                _run_quickstart_adapter(
                    repo_root=repo_root,
                    scenario_artifact_dir=quickstart_artifact_dir,
                    scenario_state_dir=quickstart_state_dir,
                    adapter_input_path=adapter_input_path,
                    adapter_output_path=adapter_execution_report_path,
                )
                adapter_finished_at = _utc_now()
                adapter_status_path = _run_quickstart_status(
                    repo_root=repo_root,
                    scenario_artifact_dir=quickstart_artifact_dir,
                    scenario_state_dir=quickstart_state_dir,
                    status_output_path=status_output_path,
                )
                adapter_report = _load_json(adapter_execution_report_path)
                adapter_status = _load_json(adapter_status_path)
                _append_timeline(
                    timeline=timeline,
                    sequence=sequence,
                    scenario_id=scenario_id,
                    phase="ADAPTER",
                    status="COMPLETED",
                    started_at=adapter_started_at,
                    finished_at=adapter_finished_at,
                    artifact_path=_relative_path(adapter_execution_report_path, repo_root),
                    detail=_quickstart_adapter_timeline_detail(
                        scenario_id,
                        adapter_report,
                    ),
                )
                _validate_quickstart_adapter_result(
                    scenario_id=scenario_id,
                    adapter_report=adapter_report,
                    adapter_status=adapter_status,
                    expected=expected,
                )
            else:
                adapter_status_started_at = _utc_now()
                adapter_status_path = _run_quickstart_status(
                    repo_root=repo_root,
                    scenario_artifact_dir=quickstart_artifact_dir,
                    scenario_state_dir=quickstart_state_dir,
                    status_output_path=status_output_path,
                )
                adapter_status_finished_at = _utc_now()
                adapter_status = _load_json(adapter_status_path)
                _append_timeline(
                    timeline=timeline,
                    sequence=sequence,
                    scenario_id=scenario_id,
                    phase="ADAPTER",
                    status="SKIPPED",
                    started_at=adapter_status_started_at,
                    finished_at=adapter_status_finished_at,
                    artifact_path=_relative_path(adapter_status_path, repo_root),
                    detail=(
                        f"Did not invoke the adapter for scenario {scenario_id} because "
                        "the Quickstart return flow blocked before a trusted release handoff."
                    ),
                )
                _validate_quickstart_blocked_status(
                    scenario_id=scenario_id,
                    adapter_status=adapter_status,
                    expected=expected,
                )

    observed_reason_codes = sorted(
        set(_policy_reason_codes(policy_report))
        | set(_return_optimization_reason_codes(optimization_report))
        | set(_workflow_reason_codes(workflow_result, scenario_mode=scenario_mode))
        | set(_adapter_reason_codes(adapter_report, scenario_mode=scenario_mode))
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
            runtime_mode=runtime_mode,
            policy_report=policy_report,
            optimization_report=optimization_report,
            workflow_result=workflow_result,
            adapter_report=adapter_report,
            adapter_status=adapter_status,
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
            None if workflow_result_path is None else _relative_path(workflow_result_path, repo_root)
        ),
        "quickstartSeedReceiptPath": (
            None
            if quickstart_seed_receipt_path is None
            else _relative_path(quickstart_seed_receipt_path, repo_root)
        ),
        "adapterExecutionReportPath": (
            None
            if adapter_execution_report_path is None
            else _relative_path(adapter_execution_report_path, repo_root)
        ),
        "adapterStatusPath": (
            None if adapter_status_path is None else _relative_path(adapter_status_path, repo_root)
        ),
        "workflowRuntime": None if workflow_result is None else runtime_mode,
        "policyDecision": policy_report["overallDecision"],
        "optimizationStatus": (
            None if optimization_report is None else optimization_report["status"]
        ),
        "currentPostedLotIds": (
            [] if obligation is None else sorted(obligation.get("currentPostedLotIds", []))
        ),
        "retainedLotIds": retained_lot_ids,
        "returnLotIds": return_lot_ids,
        "requestedReturnQuantity": requested_return_quantity,
        "remainingRequiredCoverage": remaining_required_coverage,
        "blockedPhase": _blocked_phase(
            runtime_mode=runtime_mode,
            scenario_mode=scenario_mode,
            policy_report=policy_report,
            optimization_report=optimization_report,
            workflow_result=workflow_result,
            adapter_report=adapter_report,
        ),
        "adapterOutcome": _adapter_outcome(
            runtime_mode=runtime_mode,
            workflow_result=workflow_result,
            adapter_report=adapter_report,
        ),
        "requestIdentifier": (
            None
            if workflow_result is None
            else workflow_result.get("returnRequestId")
        ),
        "approvalState": _build_approval_state(workflow_result),
        "releaseAction": _build_release_action(workflow_result, adapter_report),
        "finalPostReturnState": _build_final_post_return_state(
            runtime_mode=runtime_mode,
            workflow_result=workflow_result,
            adapter_status=adapter_status,
        ),
        "replayHandlingResult": _build_replay_handling_result(
            scenario=scenario,
            workflow_result=workflow_result,
            adapter_report=adapter_report,
        ),
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

    current_secured_amount = round(sum(lot["quantity"] for lot in current_posted_lots), 2)
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


def _build_quickstart_workflow_request(
    *,
    scenario: dict[str, Any],
    obligation: dict[str, Any],
    policy: dict[str, Any],
    optimization_report: dict[str, Any],
    seed_receipt: dict[str, Any],
) -> dict[str, Any]:
    recommended_portfolio = optimization_report["recommendedPortfolio"]
    recommendation = optimization_report["substitutionRecommendation"]
    if recommended_portfolio is None or recommendation is None:
        raise DemoExecutionError(
            f"{scenario['scenarioId']}: Quickstart workflow requested without a retained-set recommendation"
        )

    current_posted_lot_ids = obligation["currentPostedLotIds"]
    seed_current_lots = seed_receipt["currentEncumberedLots"]
    seed_current_lots_by_id = {lot["lotId"]: lot for lot in seed_current_lots}
    selected_return_lot_ids = recommendation["removeLotIds"]
    if not selected_return_lot_ids:
        raise DemoExecutionError(
            f"{scenario['scenarioId']}: optimizer did not select any Quickstart return lots"
        )

    _assert_equal(
        actual=sorted(current_posted_lot_ids),
        expected=sorted(seed_current_lots_by_id),
        message=(
            f"{scenario['scenarioId']}: currently encumbered lot scope drifted from the "
            "declared Quickstart return seed scenario"
        ),
    )
    _assert_equal(
        actual=obligation["obligationId"],
        expected=seed_receipt["obligationId"],
        message=f"{scenario['scenarioId']}: obligation id drifted from the Quickstart seed receipt",
    )

    return_lots = [seed_current_lots_by_id[lot_id] for lot_id in selected_return_lot_ids]
    workflow_config = scenario["workflow"]

    return {
        "scenarioId": scenario["scenarioId"],
        "obligationId": seed_receipt["obligationId"],
        "returnRequestId": workflow_config.get(
            "returnRequestId",
            f"{seed_receipt['correlationId']}-return",
        ),
        "correlationId": seed_receipt["correlationId"],
        "policyVersion": seed_receipt["policyVersion"],
        "snapshotId": seed_receipt["snapshotId"],
        "decisionReference": seed_receipt["decisionReference"],
        "providerParty": seed_receipt["providerParty"],
        "securedParty": seed_receipt["securedParty"],
        "custodianParty": seed_receipt["custodianParty"],
        "currentEncumberedLotIds": current_posted_lot_ids,
        "returnLots": return_lots,
        "currentSecuredAmount": round(sum(lot["quantity"] for lot in seed_current_lots), 2),
        "remainingRequiredCoverage": workflow_config.get(
            "remainingRequiredCoverageOverride", obligation["obligationAmount"]
        ),
        "requiresSecuredPartyApproval": policy["substitutionRights"][
            "requiresSecuredPartyConsent"
        ],
        "requiresCustodianApproval": policy["substitutionRights"][
            "requiresCustodianConsent"
        ],
        "workflowGate": scenario["workflowGate"],
    }


def _build_quickstart_adapter_input(
    *,
    seed_receipt: dict[str, Any],
    workflow_request: dict[str, Any],
    workflow_result: dict[str, Any],
    simulate_replay_attempt: bool,
) -> dict[str, Any]:
    settlement_instruction_id = workflow_result.get("settlementInstructionId")
    if settlement_instruction_id is None:
        raise DemoExecutionError(
            f"{workflow_result['scenarioId']}: Quickstart return adapter requested without a settlement instruction"
        )

    return {
        "scenarioId": workflow_result["scenarioId"],
        "obligationId": seed_receipt["obligationId"],
        "returnRequestId": workflow_result["returnRequestId"],
        "providerParty": seed_receipt["providerParty"],
        "securedParty": seed_receipt["securedParty"],
        "custodianParty": seed_receipt["custodianParty"],
        "settlementInstructionId": settlement_instruction_id,
        "currentEncumberedLots": seed_receipt["currentEncumberedLots"],
        "returnLots": workflow_request["returnLots"],
        "simulateReplayAttempt": simulate_replay_attempt,
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


def _validate_ide_workflow_result(
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


def _validate_quickstart_workflow_result(
    *,
    scenario_id: str,
    workflow_result: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    _assert_equal(
        actual=workflow_result["returnState"],
        expected=expected["workflowReturnState"],
        message=f"{scenario_id}: unexpected Quickstart return state",
    )
    _assert_equal(
        actual=workflow_result["workflowGate"],
        expected=expected["workflowGate"],
        message=f"{scenario_id}: unexpected Quickstart return workflow gate",
    )
    _assert_equal(
        actual=workflow_result.get("settlementInstructionState"),
        expected=expected.get("workflowSettlementInstructionState"),
        message=f"{scenario_id}: unexpected Quickstart return instruction state",
    )
    _assert_equal(
        actual=sorted(workflow_result["currentEncumberedLotIds"]),
        expected=sorted(expected["currentEncumberedLotIds"]),
        message=f"{scenario_id}: current encumbered Quickstart lot set drifted from expectation",
    )
    _assert_equal(
        actual=sorted(workflow_result["returnedLotIds"]),
        expected=sorted(expected["returnedLotIds"]),
        message=f"{scenario_id}: Quickstart returned lot set drifted from expectation",
    )
    _assert_equal(
        actual=sorted(workflow_result["remainingEncumberedLotIds"]),
        expected=sorted(expected["remainingEncumberedLotIds"]),
        message=f"{scenario_id}: Quickstart remaining encumbered set drifted from expectation",
    )
    _assert_equal(
        actual=workflow_result["releaseConditionSatisfied"],
        expected=expected["releaseConditionSatisfied"],
        message=f"{scenario_id}: Quickstart release-condition result drifted from expectation",
    )
    _assert_equal(
        actual=workflow_result["atomicityOutcome"],
        expected=expected["atomicityOutcome"],
        message=f"{scenario_id}: Quickstart atomicity outcome drifted from expectation",
    )
    if "requiredControlChecks" in expected:
        _assert_equal(
            actual=sorted(check["checkId"] for check in workflow_result["controlChecks"]),
            expected=sorted(expected["requiredControlChecks"]),
            message=f"{scenario_id}: Quickstart workflow control checks drifted from expectation",
        )
    if workflow_result["executionReportCount"] < expected["minimumExecutionReportCount"]:
        raise DemoExecutionError(
            f"{scenario_id}: expected at least {expected['minimumExecutionReportCount']} "
            f"Quickstart execution reports but found {workflow_result['executionReportCount']}"
        )


def _validate_quickstart_adapter_result(
    *,
    scenario_id: str,
    adapter_report: dict[str, Any],
    adapter_status: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    adapter_movement_lot_ids = [
        movement["lotId"] for movement in adapter_report["adapterReceipt"]["movements"]
    ]
    _assert_equal(
        actual=adapter_report["adapterReceipt"]["status"],
        expected=expected["adapterReceiptStatus"],
        message=f"{scenario_id}: unexpected return adapter receipt status",
    )
    _assert_equal(
        actual=sorted(adapter_report["approvedReturnLotIds"]),
        expected=sorted(expected["adapterReturnLotIds"]),
        message=f"{scenario_id}: Quickstart adapter return scope drifted from expectation",
    )
    _assert_equal(
        actual=sorted(adapter_movement_lot_ids),
        expected=sorted(expected["adapterReturnLotIds"]),
        message=f"{scenario_id}: Quickstart adapter movement scope drifted from expectation",
    )
    _assert_equal(
        actual=adapter_report["workflowConfirmation"]["returnStateAfterConfirmation"],
        expected=expected["adapterReturnStateAfterConfirmation"],
        message=f"{scenario_id}: unexpected return state after adapter confirmation",
    )
    _assert_equal(
        actual=adapter_report["workflowConfirmation"]["settledInstructionState"],
        expected=expected["adapterSettledInstructionState"],
        message=f"{scenario_id}: unexpected return instruction state after adapter confirmation",
    )
    _assert_equal(
        actual=sorted(adapter_report["workflowConfirmation"]["returnedLotIds"]),
        expected=sorted(expected["finalReturnedLotIds"]),
        message=f"{scenario_id}: final returned encumbrance set drifted from expectation",
    )
    _assert_equal(
        actual=sorted(adapter_report["workflowConfirmation"]["remainingEncumberedLotIds"]),
        expected=sorted(expected["finalRemainingEncumberedLotIds"]),
        message=f"{scenario_id}: final remaining encumbered set drifted from expectation",
    )
    _assert_equal(
        actual=adapter_status["returnState"],
        expected=expected["adapterReturnStateAfterConfirmation"],
        message=f"{scenario_id}: provider-visible return state drifted from adapter confirmation",
    )
    _assert_equal(
        actual=adapter_status["settlementInstructionState"],
        expected=expected["adapterSettledInstructionState"],
        message=f"{scenario_id}: provider-visible settlement instruction state drifted from adapter confirmation",
    )
    _assert_equal(
        actual=sorted(
            _encumbrance_lot_ids_with_status(
                adapter_status["providerVisibleEncumbrances"],
                "EncumbranceReleased",
            )
        ),
        expected=sorted(expected["finalReturnedLotIds"]),
        message=f"{scenario_id}: provider-visible released encumbrance set drifted from expectation",
    )
    _assert_equal(
        actual=sorted(
            _encumbrance_lot_ids_with_status(
                adapter_status["providerVisibleEncumbrances"],
                "EncumbrancePledged",
            )
        ),
        expected=sorted(expected["finalRemainingEncumberedLotIds"]),
        message=f"{scenario_id}: provider-visible remaining encumbrance set drifted from expectation",
    )
    _assert_equal(
        actual=sorted(
            _holding_lot_ids_with_control_state(
                adapter_status["providerVisibleCurrentLotHoldings"],
                "ReturnedToProviderAccount",
            )
        ),
        expected=sorted(expected["finalReturnedHoldingLotIds"]),
        message=f"{scenario_id}: provider-visible returned holding set drifted from expectation",
    )
    _assert_equal(
        actual=sorted(
            _holding_lot_ids_with_control_state(
                adapter_status["providerVisibleCurrentLotHoldings"],
                "SettledToSecuredAccount",
            )
        ),
        expected=sorted(expected["finalRemainingHoldingLotIds"]),
        message=f"{scenario_id}: provider-visible retained holding set drifted from expectation",
    )
    _assert_equal(
        actual=len(adapter_status["providerVisibleAdapterReceipts"]),
        expected=1,
        message=f"{scenario_id}: expected exactly one provider-visible return adapter receipt",
    )
    _assert_equal(
        actual=adapter_report["replayHandling"]["result"],
        expected=expected["adapterReplayHandlingResult"],
        message=f"{scenario_id}: replay handling result drifted from expectation",
    )


def _validate_quickstart_blocked_status(
    *,
    scenario_id: str,
    adapter_status: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    _assert_equal(
        actual=adapter_status["returnState"],
        expected=expected["blockedReturnState"],
        message=f"{scenario_id}: unexpected return state for blocked Quickstart path",
    )
    if "workflowSettlementInstructionState" in expected:
        _assert_equal(
            actual=adapter_status["settlementInstructionState"],
            expected=expected["workflowSettlementInstructionState"],
            message=f"{scenario_id}: blocked Quickstart instruction state drifted from expectation",
        )
    _assert_equal(
        actual=sorted(
            _encumbrance_lot_ids_with_status(
                adapter_status["providerVisibleEncumbrances"],
                "EncumbranceReleased",
            )
        ),
        expected=sorted(expected["blockedReturnedLotIds"]),
        message=f"{scenario_id}: blocked path released encumbrances unexpectedly",
    )
    _assert_equal(
        actual=sorted(
            _encumbrance_lot_ids_with_status(
                adapter_status["providerVisibleEncumbrances"],
                "EncumbrancePledged",
            )
        ),
        expected=sorted(expected["blockedRemainingEncumberedLotIds"]),
        message=f"{scenario_id}: blocked path changed the remaining encumbrance set unexpectedly",
    )
    _assert_equal(
        actual=sorted(
            holding["lotId"] for holding in adapter_status["providerVisibleCurrentLotHoldings"]
        ),
        expected=sorted(expected["blockedHoldingLotIds"]),
        message=f"{scenario_id}: blocked path changed the provider-visible holding set unexpectedly",
    )
    _assert_equal(
        actual=len(adapter_status["providerVisibleAdapterReceipts"]),
        expected=0,
        message=f"{scenario_id}: adapter receipts were emitted even though the return was blocked",
    )


def _run_quickstart_seed(
    *,
    repo_root: Path,
    scenario_artifact_dir: Path,
    scenario_state_dir: Path,
    quickstart_manifest_path: Path,
) -> Path:
    env = _localnet_env(
        repo_root=repo_root,
        scenario_artifact_dir=scenario_artifact_dir,
        scenario_state_dir=scenario_state_dir,
        quickstart_manifest_path=quickstart_manifest_path,
    )
    _run_command(
        command=[str(repo_root / "scripts/localnet-seed-return-demo.sh")],
        env=env,
        cwd=repo_root,
        error_label="localnet-seed-return-demo",
    )
    receipt_path = scenario_artifact_dir / "localnet-control-plane-seed-receipt.json"
    if not receipt_path.is_file():
        raise DemoExecutionError(
            "localnet-seed-return-demo did not produce "
            + receipt_path.relative_to(repo_root).as_posix()
        )
    return receipt_path


def _run_quickstart_workflow(
    *,
    repo_root: Path,
    scenario_artifact_dir: Path,
    scenario_state_dir: Path,
    workflow_input_path: Path,
    workflow_result_path: Path,
) -> dict[str, Any]:
    env = _localnet_env(
        repo_root=repo_root,
        scenario_artifact_dir=scenario_artifact_dir,
        scenario_state_dir=scenario_state_dir,
        quickstart_manifest_path=None,
    )
    _run_command(
        command=[
            str(repo_root / "scripts/localnet-run-return-workflow.sh"),
            "--input-file",
            str(workflow_input_path),
            "--output-file",
            str(workflow_result_path),
        ],
        env=env,
        cwd=repo_root,
        error_label="localnet-run-return-workflow",
    )
    return _load_json(workflow_result_path)


def _run_quickstart_adapter(
    *,
    repo_root: Path,
    scenario_artifact_dir: Path,
    scenario_state_dir: Path,
    adapter_input_path: Path,
    adapter_output_path: Path,
) -> None:
    env = _localnet_env(
        repo_root=repo_root,
        scenario_artifact_dir=scenario_artifact_dir,
        scenario_state_dir=scenario_state_dir,
        quickstart_manifest_path=None,
    )
    _run_command(
        command=[
            str(repo_root / "scripts/localnet-run-return-token-adapter.sh"),
            "--input-file",
            str(adapter_input_path),
            "--output-file",
            str(adapter_output_path),
        ],
        env=env,
        cwd=repo_root,
        error_label="localnet-run-return-token-adapter",
    )


def _run_quickstart_status(
    *,
    repo_root: Path,
    scenario_artifact_dir: Path,
    scenario_state_dir: Path,
    status_output_path: Path,
) -> Path:
    env = _localnet_env(
        repo_root=repo_root,
        scenario_artifact_dir=scenario_artifact_dir,
        scenario_state_dir=scenario_state_dir,
        quickstart_manifest_path=None,
    )
    _run_command(
        command=[
            str(repo_root / "scripts/localnet-return-status.sh"),
            "--output-file",
            str(status_output_path),
        ],
        env=env,
        cwd=repo_root,
        error_label="localnet-return-status",
    )
    if not status_output_path.is_file():
        raise DemoExecutionError(
            "localnet-return-status did not produce "
            + status_output_path.relative_to(repo_root).as_posix()
        )
    return status_output_path


def _workflow_reason_codes(
    workflow_result: dict[str, Any] | None,
    *,
    scenario_mode: str,
) -> list[str]:
    if workflow_result is None or scenario_mode != "NEGATIVE":
        return []
    return sorted(check["checkId"] for check in workflow_result["controlChecks"])


def _adapter_reason_codes(
    adapter_report: dict[str, Any] | None,
    *,
    scenario_mode: str,
) -> list[str]:
    if adapter_report is None or scenario_mode != "NEGATIVE":
        return []
    replay = adapter_report.get("replayHandling")
    if replay is None:
        return []
    control_check_id = replay.get("controlCheckId")
    return [] if control_check_id is None else [control_check_id]


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


def _ide_workflow_timeline_detail(
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


def _quickstart_workflow_timeline_detail(
    scenario_id: str,
    workflow_result: dict[str, Any],
) -> str:
    if (
        workflow_result["returnState"] == "PendingSettlement"
        and workflow_result["workflowGate"] == "PREPARE_FOR_ADAPTER"
    ):
        return (
            f"Prepared the Quickstart return workflow for scenario {scenario_id} "
            "and exposed the approved release instruction to the adapter."
        )
    return (
        f"Recorded the Quickstart return control failure for scenario {scenario_id} "
        f"with workflow state {workflow_result['returnState']}."
    )


def _quickstart_adapter_timeline_detail(
    scenario_id: str,
    adapter_report: dict[str, Any],
) -> str:
    replay_result = adapter_report["replayHandling"]["result"]
    if replay_result == "BLOCKED_DUPLICATE_RETURN_REQUEST":
        return (
            f"Executed the Quickstart return adapter for scenario {scenario_id}, "
            "settled the original release, and blocked a replayed return instruction "
            "without a second adapter side effect."
        )
    return (
        f"Executed the Quickstart return adapter for scenario {scenario_id}, "
        "released the approved holdings, and confirmed the final post-return state."
    )


def _blocked_phase(
    *,
    runtime_mode: str,
    scenario_mode: str,
    policy_report: dict[str, Any],
    optimization_report: dict[str, Any] | None,
    workflow_result: dict[str, Any] | None,
    adapter_report: dict[str, Any] | None,
) -> str | None:
    if scenario_mode != "NEGATIVE":
        return None
    if policy_report["overallDecision"] != "ACCEPT":
        return BLOCKING_POLICY
    if optimization_report is None or optimization_report["status"] != "OPTIMAL":
        return BLOCKING_OPTIMIZATION
    if runtime_mode == RUNTIME_QUICKSTART and adapter_report is not None:
        replay_result = adapter_report.get("replayHandling", {}).get("result")
        if replay_result == "BLOCKED_DUPLICATE_RETURN_REQUEST":
            return BLOCKING_ADAPTER
        return None
    return BLOCKING_WORKFLOW


def _adapter_outcome(
    *,
    runtime_mode: str,
    workflow_result: dict[str, Any] | None,
    adapter_report: dict[str, Any] | None,
) -> str | None:
    if workflow_result is None:
        return ADAPTER_NOT_REQUESTED
    if runtime_mode == RUNTIME_IDE_LEDGER:
        return ADAPTER_NOT_REQUESTED
    if adapter_report is not None:
        return ADAPTER_EXECUTED
    return ADAPTER_BLOCKED


def _build_approval_state(
    workflow_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if workflow_result is None:
        return None
    return {
        "securedPartyApproval": workflow_result["securedPartyApproval"],
        "custodianApproval": workflow_result["custodianApproval"],
        "workflowGate": workflow_result.get("workflowGate"),
        "releaseConditionSatisfied": workflow_result["releaseConditionSatisfied"],
    }


def _build_release_action(
    workflow_result: dict[str, Any] | None,
    adapter_report: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if workflow_result is None:
        return None
    if adapter_report is not None:
        return {
            "settlementInstructionId": adapter_report["settlementInstruction"]["instructionId"],
            "settlementInstructionState": adapter_report["workflowConfirmation"][
                "settledInstructionState"
            ],
            "settlementAction": adapter_report["settlementInstruction"]["settlementAction"],
            "adapterReceiptStatus": adapter_report["adapterReceipt"]["status"],
            "adapterMovementLotIds": sorted(
                movement["lotId"] for movement in adapter_report["adapterReceipt"]["movements"]
            ),
        }
    return {
        "settlementInstructionId": workflow_result.get("settlementInstructionId"),
        "settlementInstructionState": workflow_result.get("settlementInstructionState"),
        "settlementAction": (
            "ReturnCollateral"
            if workflow_result.get("settlementInstructionId") is not None
            else None
        ),
        "adapterReceiptStatus": None,
        "adapterMovementLotIds": [],
    }


def _build_final_post_return_state(
    *,
    runtime_mode: str,
    workflow_result: dict[str, Any] | None,
    adapter_status: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if runtime_mode == RUNTIME_QUICKSTART and adapter_status is not None:
        holdings = adapter_status["providerVisibleCurrentLotHoldings"]
        return {
            "returnState": adapter_status["returnState"],
            "settlementInstructionState": adapter_status["settlementInstructionState"],
            "returnedLotIds": sorted(
                _encumbrance_lot_ids_with_status(
                    adapter_status["providerVisibleEncumbrances"],
                    "EncumbranceReleased",
                )
            ),
            "remainingEncumberedLotIds": sorted(
                _encumbrance_lot_ids_with_status(
                    adapter_status["providerVisibleEncumbrances"],
                    "EncumbrancePledged",
                )
            ),
            "returnedHoldingLotIds": sorted(
                _holding_lot_ids_with_control_state(
                    holdings,
                    "ReturnedToProviderAccount",
                )
            ),
            "remainingHoldingLotIds": sorted(
                _holding_lot_ids_with_control_state(
                    holdings,
                    "SettledToSecuredAccount",
                )
            ),
            "providerVisibleAdapterReceiptCount": len(
                adapter_status["providerVisibleAdapterReceipts"]
            ),
        }
    if workflow_result is None:
        return None
    return {
        "returnState": workflow_result["returnState"],
        "settlementInstructionState": workflow_result.get("settlementInstructionState"),
        "returnedLotIds": sorted(workflow_result["returnedLotIds"]),
        "remainingEncumberedLotIds": sorted(workflow_result["remainingEncumberedLotIds"]),
        "returnedHoldingLotIds": [],
        "remainingHoldingLotIds": [],
        "providerVisibleAdapterReceiptCount": None,
    }


def _build_replay_handling_result(
    *,
    scenario: dict[str, Any],
    workflow_result: dict[str, Any] | None,
    adapter_report: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if adapter_report is not None:
        replay = adapter_report["replayHandling"]
        return {
            "attempted": replay["attempted"],
            "result": replay["result"],
            "controlCheckId": replay["controlCheckId"],
            "detail": replay["detail"],
        }
    if workflow_result is None:
        return None
    control_check_ids = {check["checkId"] for check in workflow_result["controlChecks"]}
    if "REPLAY_RETURN_BLOCKED" in control_check_ids:
        return {
            "attempted": True,
            "result": "BLOCKED_DUPLICATE_RETURN_REQUEST",
            "controlCheckId": "REPLAY_RETURN_BLOCKED",
            "detail": (
                "the workflow rejected the replayed return instruction by preserving "
                "the active request identifier after the committed release"
            ),
        }
    return {
        "attempted": scenario.get("workflow", {}).get("simulateReplayAttempt", False),
        "result": "NOT_REQUESTED",
        "controlCheckId": None,
        "detail": "no replay attempt was requested for this return path",
    }


def _encumbrance_lot_ids_with_status(
    encumbrances: list[dict[str, Any]],
    status: str,
) -> list[str]:
    return sorted(
        encumbrance["lotId"]
        for encumbrance in encumbrances
        if encumbrance["status"] == status
    )


def _holding_lot_ids_with_control_state(
    holdings: list[dict[str, Any]],
    control_state: str,
) -> list[str]:
    return sorted(
        holding["lotId"]
        for holding in holdings
        if holding["controlState"] == control_state
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
    runtime_mode: str,
    command_name: str,
) -> dict[str, Any]:
    positive_scenarios = [scenario for scenario in scenario_results if scenario["mode"] == "POSITIVE"]
    negative_scenarios = [scenario for scenario in scenario_results if scenario["mode"] == "NEGATIVE"]
    canonical = json.dumps(
        {
            "manifest": manifest,
            "runtimeMode": runtime_mode,
            "scenarioResults": scenario_results,
        },
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
            "runtimeMode": runtime_mode,
            "command": command_name,
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
    *,
    scenario_results: list[dict[str, Any]],
    runtime_mode: str,
) -> list[dict[str, Any]]:
    positive_scenario = next(
        scenario for scenario in scenario_results if scenario["mode"] == "POSITIVE"
    )
    negative_scenarios = [
        scenario for scenario in scenario_results if scenario["mode"] == "NEGATIVE"
    ]

    if runtime_mode == RUNTIME_QUICKSTART:
        replay_scenario = next(
            scenario
            for scenario in negative_scenarios
            if scenario["scenarioId"] == "negative-replayed-return-instruction-quickstart"
        )
        unauthorized_scenario = next(
            scenario
            for scenario in negative_scenarios
            if scenario["scenarioId"] == "negative-unauthorized-return-quickstart"
        )
        mismatch_scenario = next(
            scenario
            for scenario in negative_scenarios
            if scenario["scenarioId"] == "negative-obligation-state-mismatch-quickstart"
        )
        negative_evidence = _compact_paths(
            path
            for scenario in negative_scenarios
            for path in (
                scenario["policyEvaluationReportPath"],
                scenario["workflowResultPath"],
                scenario["adapterExecutionReportPath"],
                scenario["adapterStatusPath"],
            )
        )
        return [
            {
                "invariantId": "PDR-001",
                "status": "PASS",
                "evidence": [positive_scenario["policyEvaluationReportPath"]],
                "note": "The positive Quickstart return path used a generated policy-evaluation report derived from declared inputs.",
            },
            {
                "invariantId": "ALLOC-001",
                "status": "PASS",
                "evidence": [positive_scenario["optimizationReportPath"]],
                "note": "The optimizer selected the retained set deterministically and the Quickstart return release scope matched that recommendation.",
            },
            {
                "invariantId": "WF-001",
                "status": "PASS",
                "evidence": _compact_paths(
                    [
                        positive_scenario["quickstartSeedReceiptPath"],
                        positive_scenario["workflowResultPath"],
                    ]
                ),
                "note": "The Quickstart return workflow remained authoritative for request identity, approvals, settlement intent, and final workflow closure.",
            },
            {
                "invariantId": "CTRL-001",
                "status": "PASS",
                "evidence": _compact_paths(
                    [
                        positive_scenario["workflowResultPath"],
                        unauthorized_scenario["workflowResultPath"],
                        unauthorized_scenario["adapterStatusPath"],
                        mismatch_scenario["workflowResultPath"],
                        mismatch_scenario["adapterStatusPath"],
                    ]
                ),
                "note": "Quickstart blocked unauthorized release confirmation and stale obligation-state return attempts before any unintended adapter mutation could commit.",
            },
            {
                "invariantId": "ADAPT-001",
                "status": "PASS",
                "evidence": _compact_paths(
                    [
                        positive_scenario["workflowResultPath"],
                        positive_scenario["adapterExecutionReportPath"],
                        positive_scenario["adapterStatusPath"],
                    ]
                ),
                "note": "The reference token adapter consumed the Quickstart return handoff artifact, executed the approved release movement, and emitted an auditable receipt without bypassing workflow authority.",
            },
            {
                "invariantId": "ATOM-001",
                "status": "PASS",
                "evidence": _compact_paths(
                    [
                        positive_scenario["adapterExecutionReportPath"],
                        positive_scenario["adapterStatusPath"],
                        unauthorized_scenario["adapterStatusPath"],
                        mismatch_scenario["adapterStatusPath"],
                    ]
                ),
                "note": "The positive Quickstart path released only the approved return scope, and the blocked negative paths preserved the incumbent encumbrance and holding state with zero adapter receipts.",
            },
            {
                "invariantId": "REPL-001",
                "status": "PASS",
                "evidence": _compact_paths(
                    [
                        replay_scenario["workflowResultPath"],
                        replay_scenario["adapterExecutionReportPath"],
                        replay_scenario["adapterStatusPath"],
                    ]
                ),
                "note": "The replay scenario settled the original return once, then blocked a duplicate request identifier without a second adapter release side effect.",
            },
            {
                "invariantId": "REPT-001",
                "status": "PASS",
                "evidence": _compact_paths(
                    [
                        positive_scenario["policyEvaluationReportPath"],
                        positive_scenario["optimizationReportPath"],
                        positive_scenario["workflowResultPath"],
                        positive_scenario["adapterExecutionReportPath"],
                        positive_scenario["adapterStatusPath"],
                    ]
                ),
                "note": "The Quickstart return report references real policy, optimization, workflow, adapter, and provider-visible status artifacts rather than operator-authored summaries.",
            },
            {
                "invariantId": "EXCP-001",
                "status": "PASS",
                "evidence": negative_evidence,
                "note": "The negative Quickstart return scenarios failed deterministically for unauthorized release, replay, and stale obligation-state mismatch without fabricating downstream success.",
            },
        ]

    replay_scenario = next(
        scenario
        for scenario in negative_scenarios
        if scenario["scenarioId"] == "negative-replayed-return-instruction"
    )
    negative_workflow_evidence = [
        scenario["workflowResultPath"]
        for scenario in negative_scenarios
        if scenario["workflowResultPath"] is not None
    ]
    negative_artifact_evidence = _compact_paths(
        artifact
        for scenario in negative_scenarios
        for artifact in (
            scenario["policyEvaluationReportPath"],
            scenario["optimizationReportPath"],
            scenario["workflowResultPath"],
        )
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
            "evidence": _compact_paths(negative_workflow_evidence),
            "note": "The return workflow blocked unauthorized release, replay, and obligation-state mismatch paths with explicit control checks instead of silently mutating encumbrance state.",
        },
        {
            "invariantId": "ATOM-001",
            "status": "PASS",
            "evidence": _compact_paths(
                [positive_scenario["workflowResultPath"], *negative_workflow_evidence]
            ),
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
            "evidence": _compact_paths(
                [
                    positive_scenario["workflowResultPath"],
                    positive_scenario["policyEvaluationReportPath"],
                    positive_scenario["optimizationReportPath"],
                ]
            ),
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
    if optimization_report is not None:
        recommendation = optimization_report["substitutionRecommendation"]
        if recommendation is not None:
            return (
                sorted(recommendation["recommendedLotIds"]),
                sorted(recommendation["removeLotIds"]),
            )

    if workflow_request is None:
        return [], []

    current_lot_ids = (
        workflow_request["currentEncumberedLotIds"]
        if "currentEncumberedLotIds" in workflow_request
        else [lot["lotId"] for lot in workflow_request["currentPostedLots"]]
    )
    return_lot_ids = sorted(lot["lotId"] for lot in workflow_request["returnLots"])
    retained_lot_ids = sorted(
        lot_id for lot_id in current_lot_ids if lot_id not in set(return_lot_ids)
    )
    return retained_lot_ids, return_lot_ids


def _scenario_summary(
    *,
    scenario: dict[str, Any],
    runtime_mode: str,
    policy_report: dict[str, Any],
    optimization_report: dict[str, Any] | None,
    workflow_result: dict[str, Any] | None,
    adapter_report: dict[str, Any] | None,
    adapter_status: dict[str, Any] | None,
) -> str:
    if scenario["mode"] == "POSITIVE":
        assert workflow_result is not None
        if runtime_mode == RUNTIME_QUICKSTART:
            assert adapter_report is not None
            return (
                "Quickstart prepared return request "
                + workflow_result["returnRequestId"]
                + ", the adapter released "
                + ", ".join(sorted(adapter_report["approvedReturnLotIds"]))
                + ", and Canton closed the return with replay handling "
                + adapter_report["replayHandling"]["result"]
                + "."
            )
        return (
            f"The optimizer retained {', '.join(sorted(set(workflow_result['remainingEncumberedLotIds'])))} "
            f"and the Daml workflow closed the return for "
            f"{', '.join(sorted(workflow_result['returnedLotIds']))}."
        )

    if runtime_mode == RUNTIME_QUICKSTART and adapter_report is not None and adapter_status is not None:
        return (
            "Quickstart settled the original return for request "
            + workflow_result["returnRequestId"]
            + ", then blocked the duplicate replay attempt with result "
            + adapter_report["replayHandling"]["result"]
            + " while keeping provider-visible adapter receipts at "
            + str(len(adapter_status["providerVisibleAdapterReceipts"]))
            + "."
        )

    if runtime_mode == RUNTIME_QUICKSTART and workflow_result is not None and adapter_status is not None:
        control_codes = ", ".join(check["checkId"] for check in workflow_result["controlChecks"])
        return (
            "Quickstart blocked the return at workflow state "
            + workflow_result["returnState"]
            + " with control checks "
            + control_codes
            + " and provider-visible adapter receipts "
            + str(len(adapter_status["providerVisibleAdapterReceipts"]))
            + "."
        )

    if workflow_result is not None:
        control_codes = ", ".join(check["checkId"] for check in workflow_result["controlChecks"])
        return (
            f"The workflow ended in state {workflow_result['returnState']} with control "
            f"checks {control_codes}."
        )

    if optimization_report is None:
        return (
            f"Policy evaluation blocked the return path with decision "
            f"{policy_report['overallDecision']} and reason codes "
            f"{', '.join(_policy_reason_codes(policy_report))}."
        )

    return (
        f"Policy evaluation remained admissible, but optimization ended with "
        f"{optimization_report['status']} and reason codes "
        f"{', '.join(_return_optimization_reason_codes(optimization_report))}."
    )


def _default_command_name(runtime_mode: str) -> str:
    if runtime_mode == RUNTIME_QUICKSTART:
        return "make demo-return-quickstart"
    return "make demo-return"


def _default_report_basename(runtime_mode: str) -> str:
    if runtime_mode == RUNTIME_QUICKSTART:
        return "return-quickstart"
    return "return-demo"


def _write_markdown_summary(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Return Demo Summary",
        "",
        f"- Report ID: `{report['returnReportId']}`",
        f"- Runtime mode: `{report['demo']['runtimeMode']}`",
        f"- Command: `{report['demo']['command']}`",
        f"- Manifest: `{report['demo']['manifestPath']}`",
        f"- Report artifact: `{report['artifacts']['returnReportPath']}`",
        "",
        "## Scenario Outcomes",
        "",
        "| Scenario | Mode | Result | Blocked Phase | Adapter Outcome | Request | Replay | Summary |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for scenario in report["scenarios"]:
        replay = scenario["replayHandlingResult"]
        lines.append(
            f"| {scenario['scenarioId']} | {scenario['mode']} | {scenario['result']} | "
            f"{scenario['blockedPhase'] or '-'} | {scenario['adapterOutcome'] or '-'} | "
            f"{scenario['requestIdentifier'] or '-'} | "
            f"{'-' if replay is None else replay['result']} | {scenario['summary']} |"
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
    for check in report["invariantChecks"]:
        evidence = ", ".join(f"`{item}`" for item in check["evidence"])
        lines.append(
            f"| {check['invariantId']} | {check['status']} | {evidence} | {check['note']} |"
        )

    _write_text(path, "\n".join(lines) + "\n")


def _write_timeline_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        "# Return Demo Timeline",
        "",
        "| Seq | Scenario | Phase | Status | Artifact | Detail |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in report["timeline"]:
        artifact = "`-`" if entry["artifactPath"] is None else f"`{entry['artifactPath']}`"
        lines.append(
            f"| {entry['sequence']} | {entry['scenarioId']} | {entry['phase']} | {entry['status']} | {artifact} | {entry['detail']} |"
        )
    _write_text(path, "\n".join(lines) + "\n")
