"""CLI entrypoint for deterministic collateral optimization."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from optimizer import (
    InventoryInputError,
    OptimizationInputError,
    default_output_path,
    load_json,
    optimize_collateral,
    write_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Optimize collateral allocation for one policy, inventory snapshot, and obligation."
        )
    )
    parser.add_argument("--policy", required=True, help="Path to the CPL policy JSON file.")
    parser.add_argument(
        "--inventory",
        required=True,
        help="Path to the candidate inventory JSON file.",
    )
    parser.add_argument(
        "--obligation",
        required=True,
        help="Path to the obligation JSON file.",
    )
    parser.add_argument(
        "--output",
        help="Optional output path for the generated optimization report.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        policy = load_json(args.policy)
        inventory = load_json(args.inventory)
        obligation = load_json(args.obligation)
        report = optimize_collateral(policy, inventory, obligation)
    except (OSError, ValueError, InventoryInputError, OptimizationInputError) as exc:
        print(f"optimize: {exc}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else default_output_path(report)
    written_path = write_report(report, output_path)
    print(written_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
