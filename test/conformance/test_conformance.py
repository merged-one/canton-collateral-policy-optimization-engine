import json
import os
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "app/orchestration"))

from conformance_suite import REQUIRED_CHECK_IDS, run_conformance_suite  # noqa: E402


class ConformanceSuiteTest(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.output_dir = REPO_ROOT / "reports/generated"
        cls.report_path = cls.output_dir / "conformance-suite-report.json"

        if cls.report_path.is_file():
            cls.report = cls.load_json(cls.report_path)
        else:
            missing_env = [
                name
                for name in ("DAML_BIN", "CHECK_JSONSCHEMA_BIN")
                if not os.environ.get(name)
            ]
            if missing_env:
                raise unittest.SkipTest(
                    "Missing runtime environment for conformance generation: "
                    + ", ".join(missing_env)
                )
            cls.report = run_conformance_suite(
                output_dir=cls.output_dir,
                repo_root=REPO_ROOT,
            )

        cls.checks_by_id = {
            check["checkId"]: check for check in cls.report["checks"]
        }

    @staticmethod
    def load_json(path: Path) -> dict:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_overall_status_is_pass(self) -> None:
        self.assertEqual(self.report["overallStatus"], "PASS")

    def test_required_checks_are_present(self) -> None:
        self.assertEqual(
            sorted(self.checks_by_id),
            sorted(REQUIRED_CHECK_IDS),
        )

    def test_all_checks_pass(self) -> None:
        failing = [
            check["checkId"]
            for check in self.report["checks"]
            if check["status"] != "PASS"
        ]
        self.assertEqual(failing, [])

    def test_coverage_counts_match_expected_demo_shape(self) -> None:
        self.assertEqual(self.report["coverage"]["totalScenarioCount"], 10)
        self.assertEqual(self.report["coverage"]["positiveScenarioCount"], 3)
        self.assertEqual(self.report["coverage"]["negativeScenarioCount"], 7)
        self.assertEqual(self.report["coverage"]["runtimeModes"], ["QUICKSTART"])

    def test_demo_reports_are_indexed(self) -> None:
        self.assertEqual(len(self.report["demoReports"]), 3)
        for demo_report in self.report["demoReports"]:
            self.assertTrue((REPO_ROOT / demo_report["reportPath"]).is_file())
            self.assertTrue((REPO_ROOT / demo_report["summaryPath"]).is_file())
            self.assertTrue((REPO_ROOT / demo_report["timelinePath"]).is_file())
            self.assertEqual(demo_report["runtimeMode"], "QUICKSTART")

    def test_runtime_evidence_is_indexed(self) -> None:
        runtime_evidence = self.report["runtimeEvidence"]
        self.assertEqual(runtime_evidence["runtimeMode"], "QUICKSTART")
        self.assertEqual(runtime_evidence["validationFailures"], [])
        for field in (
            "deploymentReceiptPath",
            "deploymentSummaryPath",
            "referenceAdapterExecutionReportPath",
            "referenceAdapterStatusPath",
            "referenceAdapterSummaryPath",
        ):
            self.assertTrue((REPO_ROOT / runtime_evidence[field]).is_file())


if __name__ == "__main__":
    unittest.main()
