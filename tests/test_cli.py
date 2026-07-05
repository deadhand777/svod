"""Tests for the CLI."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from svod import main
from svod._internal import debug

if TYPE_CHECKING:
    from pathlib import Path


def test_main() -> None:
    """Basic CLI test."""
    assert main([]) == 0


def test_show_help(capsys: pytest.CaptureFixture) -> None:
    """Show help.

    Parameters:
        capsys: Pytest fixture to capture output.
    """
    with pytest.raises(SystemExit):
        main(["-h"])
    captured = capsys.readouterr()
    assert "svod" in captured.out


def test_show_version(capsys: pytest.CaptureFixture) -> None:
    """Show version.

    Parameters:
        capsys: Pytest fixture to capture output.
    """
    with pytest.raises(SystemExit):
        main(["-V"])
    captured = capsys.readouterr()
    assert debug._get_version() in captured.out


def test_show_debug_info(capsys: pytest.CaptureFixture) -> None:
    """Show debug information.

    Parameters:
        capsys: Pytest fixture to capture output.
    """
    with pytest.raises(SystemExit):
        main(["--debug-info"])
    captured = capsys.readouterr().out.lower()
    assert "python" in captured
    assert "system" in captured
    assert "environment" in captured
    assert "packages" in captured


def test_analyze_subcommand(synthetic_xlsx: Path, tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Analyze subcommand runs the pipeline end to end.

    Parameters:
        synthetic_xlsx: Fixture path to a synthetic raw xlsx.
        tmp_path: Pytest temporary directory.
        capsys: Pytest fixture to capture output.
    """
    exit_code = main(
        [
            "analyze",
            str(synthetic_xlsx),
            "--docs-dir",
            str(tmp_path / "docs"),
            "--report-dir",
            str(tmp_path / "report"),
            "--skip-pdf",
        ],
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "actors" in captured.out
    assert (tmp_path / "report" / "metrics.json").exists()
