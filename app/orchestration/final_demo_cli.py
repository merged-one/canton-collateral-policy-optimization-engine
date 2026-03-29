"""CLI entrypoint for the final prototype demo pack."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from final_demo_pack import build_final_demo_pack
from margin_call_demo import DemoExecutionError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build the final demo pack from the generated conformance-suite artifacts."
        )
    )
    parser.add_argument(
        "--conformance-report",
        required=True,
        help="Path to the generated conformance-suite report JSON file.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directory where generated final demo-pack artifacts should be written.",
    )
    parser.add_argument(
        "--repo-root",
        default=Path(__file__).resolve().parents[2],
        help="Repository root used for relative artifact references.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        report = build_final_demo_pack(
            conformance_report_path=args.conformance_report,
            output_dir=args.output_dir,
            repo_root=args.repo_root,
        )
    except (DemoExecutionError, OSError, ValueError) as exc:
        print(f"demo-all: {exc}", file=sys.stderr)
        return 1

    print(report["artifacts"]["finalDemoPackPath"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
