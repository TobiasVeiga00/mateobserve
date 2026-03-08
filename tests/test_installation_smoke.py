"""Smoke tests — verify MateObserve installs and wires up correctly."""

import importlib
import shutil
import sys
import subprocess as real_subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mateobserve.cli import _get_compose_file


def _find_cli() -> str | None:
    """Find the mateobserve CLI, checking the active venv first."""
    venv_bin = Path(sys.executable).parent / "mateobserve"
    if venv_bin.exists():
        return str(venv_bin)
    return shutil.which("mateobserve")


# ── Module import ────────────────────────────────────────────────────────────


def test_module_is_importable():
    mod = importlib.import_module("mateobserve")
    assert hasattr(mod, "ObserveMiddleware")
    assert hasattr(mod, "MetricsClient")
    assert hasattr(mod, "MateObserveConfig")


def test_module_has_version():
    import mateobserve
    assert hasattr(mateobserve, "__version__")
    assert isinstance(mateobserve.__version__, str)


# ── CLI entrypoint exists ────────────────────────────────────────────────────


def test_cli_entrypoint_exists():
    path = _find_cli()
    assert path is not None, "mateobserve CLI not found — is the package installed?"


# ── CLI --help ───────────────────────────────────────────────────────────────


def test_cli_help_runs():
    cli = _find_cli()
    assert cli is not None, "mateobserve CLI not found"
    result = real_subprocess.run(
        [cli, "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "mateobserve" in result.stdout.lower()
    assert "init" in result.stdout
    assert "up" in result.stdout
    assert "down" in result.stdout
    assert "status" in result.stdout


# ── CLI commands invoke correct docker compose commands ──────────────────────


EXPECTED_COMPOSE = str(_get_compose_file())


@patch("mateobserve.cli._get_compose_file", return_value=Path(EXPECTED_COMPOSE))
@patch("mateobserve.cli._ensure_env_file", return_value=Path("/tmp/test.env"))
@patch("mateobserve.cli._get_compose_cmd", return_value=["docker", "compose"])
@patch("mateobserve.cli.subprocess.run")
def test_up_calls_docker_compose_up(mock_run, mock_cmd, mock_env, mock_file):
    mock_run.return_value = MagicMock(returncode=0)

    from mateobserve.cli import cmd_up
    rc = cmd_up()

    assert rc == 0
    mock_run.assert_called_with(
        ["docker", "compose", "-f", EXPECTED_COMPOSE, "--env-file", "/tmp/test.env", "up", "-d"]
    )


@patch("mateobserve.cli._get_compose_file", return_value=Path(EXPECTED_COMPOSE))
@patch("mateobserve.cli._env_file_path")
@patch("mateobserve.cli._get_compose_cmd", return_value=["docker", "compose"])
@patch("mateobserve.cli.subprocess.run")
def test_down_calls_docker_compose_down(mock_run, mock_cmd, mock_env_path, mock_file):
    mock_env_path.return_value = MagicMock(exists=MagicMock(return_value=True), **{"__str__": lambda s: "/tmp/test.env"})
    mock_run.return_value = MagicMock(returncode=0)

    from mateobserve.cli import cmd_down
    rc = cmd_down()

    assert rc == 0
    mock_run.assert_called_with(
        ["docker", "compose", "-f", EXPECTED_COMPOSE, "--env-file", "/tmp/test.env", "down"]
    )


@patch("mateobserve.cli._env_file_path")
@patch("mateobserve.cli.subprocess.run")
def test_status_calls_docker_compose_ps(mock_run, mock_env_path):
    mock_env_path.return_value = MagicMock(exists=MagicMock(return_value=True), **{"__str__": lambda s: "/tmp/test.env"})
    mock_run.return_value = MagicMock(returncode=0)

    from mateobserve.cli import cmd_status
    rc = cmd_status()

    assert rc == 0
    # Last call should be the actual compose ps command
    mock_run.assert_called_with(
        ["docker", "compose", "-f", EXPECTED_COMPOSE, "--env-file", "/tmp/test.env", "ps"]
    )


# ── CLI propagates failures ──────────────────────────────────────────────────


@patch("mateobserve.cli._ensure_env_file", return_value="/tmp/test.env")
@patch("mateobserve.cli.subprocess.run")
def test_up_propagates_nonzero_exit(mock_run, mock_env):
    mock_run.return_value = MagicMock(returncode=1)

    from mateobserve.cli import cmd_up
    assert cmd_up() == 1


@patch("mateobserve.cli._env_file_path")
@patch("mateobserve.cli.subprocess.run")
def test_down_propagates_nonzero_exit(mock_run, mock_env_path):
    mock_env_path.return_value = MagicMock(exists=MagicMock(return_value=True), **{"__str__": lambda s: "/tmp/test.env"})
    mock_run.return_value = MagicMock(returncode=1)

    from mateobserve.cli import cmd_down
    assert cmd_down() == 1
