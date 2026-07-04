"""svod package.

SVOD (Subscription Video on Demand) subscribers in the USA
"""

from __future__ import annotations

from svod._internal.cli import get_parser, main

__all__: list[str] = ["get_parser", "main"]
