"""Optimizer constants for the first deterministic collateral allocator."""

from decimal import Decimal


REPORT_TYPE = "OptimizationReport"
REPORT_VERSION = "0.1.0"
OBJECTIVE_ID = "MINIMIZE_MARKET_VALUE_THEN_HAIRCUT_COST_THEN_EXCESS"
OBJECTIVE_SEQUENCE = [
    "market_value_amount",
    "haircut_cost_amount",
    "excess_amount",
    "lot_count",
    "lot_ids_lexical_tie_break",
]
DECIMAL_CENTS = Decimal("0.01")
