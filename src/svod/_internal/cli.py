# Why does this file exist, and why not put this in `__main__`?
#
# You might be tempted to import things from `__main__` later,
# but that will cause problems: the code will get executed twice:
#
# - When you run `python -m svod` python will execute
#   `__main__.py` as a script. That means there won't be any
#   `svod.__main__` in `sys.modules`.
# - When you import `__main__` it will get executed again (as a module) because
#   there's no `svod.__main__` in `sys.modules`.

from __future__ import annotations

import argparse
import sys
from typing import Any

from svod._internal import debug


class _DebugInfo(argparse.Action):
    def __init__(self, nargs: int | str | None = 0, **kwargs: Any) -> None:
        super().__init__(nargs=nargs, **kwargs)

    def __call__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ARG002
        debug._print_debug_info()
        sys.exit(0)


def get_parser() -> argparse.ArgumentParser:
    """Return the CLI argument parser.

    Returns:
        An argparse parser.
    """
    parser = argparse.ArgumentParser(prog="svod")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {debug._get_version()}")
    parser.add_argument("--debug-info", action=_DebugInfo, help="Print debug information.")
    subparsers = parser.add_subparsers(dest="command")
    analyze = subparsers.add_parser("analyze", help="Run the SVOD market analysis pipeline.")
    analyze.add_argument("xlsx", help="Path to the raw Dataxis xlsx export.")
    analyze.add_argument("--docs-dir", default="docs", help="Docs root for interactive chart HTML.")
    analyze.add_argument("--report-dir", default="report", help="Report root for PNGs, metrics and PDF.")
    analyze.add_argument("--skip-pdf", action="store_true", help="Skip typst PDF compilation.")
    return parser


def main(args: list[str] | None = None) -> int:
    """Run the main program.

    This function is executed when you type `svod` or `python -m svod`.

    Parameters:
        args: Arguments passed from the command line.

    Returns:
        An exit code.
    """
    parser = get_parser()
    opts = parser.parse_args(args=args)
    if getattr(opts, "command", None) == "analyze":
        from svod._internal.report import build_report  # noqa: PLC0415

        metrics = build_report(
            opts.xlsx,
            docs_dir=opts.docs_dir,
            report_dir=opts.report_dir,
            skip_pdf=opts.skip_pdf,
        )
        qc = metrics["qc"]
        clusters = metrics["clusters"]
        print(f"Analyzed {qc['n_actors']} actors over {len(qc['quarters'])} quarters.")
        print(f"Segments: k={clusters['k']} (silhouette {clusters['silhouette']:.2f}); artifacts written to {opts.docs_dir} and {opts.report_dir}.")
        return 0
    print(opts)
    return 0
