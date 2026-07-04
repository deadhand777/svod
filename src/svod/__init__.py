"""svod package.

SVOD (Subscription Video on Demand) subscribers in the USA
"""

from __future__ import annotations

from svod._internal.cli import get_parser, main
from svod._internal.data import QCReport, load_panel, qc_report

__all__: list[str] = ["QCReport", "get_parser", "load_panel", "main", "qc_report"]
