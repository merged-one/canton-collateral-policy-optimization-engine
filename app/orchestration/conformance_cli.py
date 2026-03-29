"""CLI entrypoint for the aggregate conformance suite."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from conformance_suite import (
    DEFAULT_MARGIN_CALL_MANIFEST,
    DEFAULT_RETURN_MANIFEST,
    DEFAULT_SUBSTITUTION_MANIFEST,
    run_conformance_suite,
)
from margin_call_demo import DemoExecutionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the aggregate conformance suite across the margin-call, substitution, and return demos."
        )
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where generated conformance artifacts should be written.",
    )
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[2],
        help="Repository root used for relative artifact references.",
    )
    parser.add_argument(
        "--margin-call-manifest",
        default=DEFAULT_MARGIN_CALL_MANIFEST,
        help="Path to the margin-call demo manifest JSON file.",
    )
    parser.add_argument(
        "--substitution-manifest",
        default=DEFAULT_SUBSTITUTION_MANIFEST,
        help="Path to the substitution demo manifest JSON file.",
    )
    parser.add_argument(
        "--return-manifest",
        default=DEFAULT_RETURN_MANIFEST,
        help="Path to the return demo manifest JSON file.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        report = run_conformance_suite(
            output_dir=args.output_dir,
            repo_root=args.repo_root,
            margin_call_manifest=args.margin_call_manifest,
            substitution_manifest=args.substitution_manifest,
            return_manifest=args.return_manifest,
        )
    except (DemoExecutionError, OSError, ValueError) as exc:
        print(f"test-conformance: {exc}", file=sys.stderr)
        return 1

    print(report["artifacts"]["conformanceReportPath"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
