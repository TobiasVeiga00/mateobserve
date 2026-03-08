"""Tests for MateObserve CLI commands."""

import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mateobserve.cli import (
    main,
    cmd_init,
    cmd_up,
    cmd_down,
    cmd_status,
    cmd_doctor,
    _get_data_dir,
    _dev_compose,
)


# ── Help ─────────────────────────────────────────────────────────────────────


def test_help_exits_cleanly():
    """mateobserve --help should print usage and exit 0."""
    with pytest.raises(SystemExit) as exc:
        with patch("sys.argv", ["mateobserve", "--help"]):
            main()
    assert exc.value.code == 0


def test_no_command_exits_with_error():
    """Running mateobserve with no subcommand should exit 1."""
    with pytest.raises(SystemExit) as exc:
        with patch("sys.argv", ["mateobserve"]):
            main()
    assert exc.value.code == 1


# ── Init ─────────────────────────────────────────────────────────────────────


@patch("mateobserve.cli._ensure_env_file")
@patch("mateobserve.cli._bundled_compose")
@patch("mateobserve.cli._get_data_dir")
def test_init_creates_stack_files(mock_data_dir, mock_bundled, mock_env, tmp_path):
    data_dir = tmp_path / ".mateobserve"
    mock_data_dir.return_value = data_dir
    bundled = tmp_path / "bundled" / "docker-compose.yml"
    bundled.parent.mkdir()
    bundled.write_text("services: {}")
    mock_bundled.return_value = bundled
    mock_env.return_value = data_dir / ".env"

    rc = cmd_init()
    assert rc == 0
    assert (data_dir / "docker-compose.yml").exists()


@patch("mateobserve.cli._bundled_compose")
@patch("mateobserve.cli._get_data_dir")
def test_init_fails_without_bundled(mock_data_dir, mock_bundled, tmp_path):
    mock_data_dir.return_value = tmp_path / ".mateobserve"
    mock_bundled.return_value = tmp_path / "nonexistent" / "docker-compose.yml"
    rc = cmd_init()
    assert rc == 1


# ── Up ───────────────────────────────────────────────────────────────────────


@patch("mateobserve.cli._get_compose_file", return_value=Path("/tmp/docker-compose.yml"))
@patch("mateobserve.cli._ensure_env_file", return_value=Path("/tmp/.env"))
@patch("mateobserve.cli._get_compose_cmd", return_value=["docker", "compose"])
@patch("mateobserve.cli.subprocess.run")
def test_up_invokes_docker_compose(mock_run, mock_compose, mock_env, mock_file):
    mock_run.return_value = MagicMock(returncode=0)
    rc = cmd_up()
    assert rc == 0
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", "/tmp/docker-compose.yml", "--env-file", "/tmp/.env", "up", "-d"]
    )


@patch("mateobserve.cli._get_compose_file", return_value=Path("/tmp/docker-compose.yml"))
@patch("mateobserve.cli._ensure_env_file", return_value=Path("/tmp/.env"))
@patch("mateobserve.cli._get_compose_cmd", return_value=["docker-compose"])
@patch("mateobserve.cli.subprocess.run")
def test_up_invokes_legacy_docker_compose(mock_run, mock_compose, mock_env, mock_file):
    mock_run.return_value = MagicMock(returncode=0)
    rc = cmd_up()
    assert rc == 0
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", "/tmp/docker-compose.yml", "--env-file", "/tmp/.env", "up", "-d"]
    )


@patch("mateobserve.cli._get_compose_file", return_value=Path("/tmp/docker-compose.yml"))
@patch("mateobserve.cli._ensure_env_file", return_value=Path("/tmp/.env"))
@patch("mateobserve.cli._get_compose_cmd", return_value=["docker", "compose"])
@patch("mateobserve.cli.subprocess.run")
def test_up_returns_nonzero_on_failure(mock_run, mock_compose, mock_env, mock_file):
    mock_run.return_value = MagicMock(returncode=1)
    rc = cmd_up()
    assert rc == 1


# ── Down ─────────────────────────────────────────────────────────────────────


@patch("mateobserve.cli._get_compose_file", return_value=Path("/tmp/docker-compose.yml"))
@patch("mateobserve.cli._env_file_path")
@patch("mateobserve.cli._get_compose_cmd", return_value=["docker", "compose"])
@patch("mateobserve.cli.subprocess.run")
def test_down_invokes_docker_compose(mock_run, mock_compose, mock_env_path, mock_file):
    mock_env_path.return_value = MagicMock(exists=MagicMock(return_value=True), **{"__str__": lambda s: "/tmp/.env"})
    mock_run.return_value = MagicMock(returncode=0)
    rc = cmd_down()
    assert rc == 0
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", "/tmp/docker-compose.yml", "--env-file", "/tmp/.env", "down"]
    )


@patch("mateobserve.cli._get_compose_file", return_value=Path("/tmp/docker-compose.yml"))
@patch("mateobserve.cli._env_file_path")
@patch("mateobserve.cli._get_compose_cmd", return_value=["docker-compose"])
@patch("mateobserve.cli.subprocess.run")
def test_down_invokes_legacy_docker_compose(mock_run, mock_compose, mock_env_path, mock_file):
    mock_env_path.return_value = MagicMock(exists=MagicMock(return_value=True), **{"__str__": lambda s: "/tmp/.env"})
    mock_run.return_value = MagicMock(returncode=0)
    rc = cmd_down()
    assert rc == 0
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", "/tmp/docker-compose.yml", "--env-file", "/tmp/.env", "down"]
    )


# ── Status ───────────────────────────────────────────────────────────────────


@patch("mateobserve.cli._get_compose_file", return_value=Path("/tmp/docker-compose.yml"))
@patch("mateobserve.cli._env_file_path")
@patch("mateobserve.cli._get_compose_cmd", return_value=["docker", "compose"])
@patch("mateobserve.cli.subprocess.run")
def test_status_invokes_docker_compose(mock_run, mock_compose, mock_env_path, mock_file):
    mock_env_path.return_value = MagicMock(exists=MagicMock(return_value=True), **{"__str__": lambda s: "/tmp/.env"})
    mock_run.return_value = MagicMock(returncode=0)
    rc = cmd_status()
    assert rc == 0
    mock_run.assert_called_once_with(
        ["docker", "compose", "-f", "/tmp/docker-compose.yml", "--env-file", "/tmp/.env", "ps"]
    )


@patch("mateobserve.cli._get_compose_file", return_value=Path("/tmp/docker-compose.yml"))
@patch("mateobserve.cli._env_file_path")
@patch("mateobserve.cli._get_compose_cmd", return_value=["docker-compose"])
@patch("mateobserve.cli.subprocess.run")
def test_status_invokes_legacy_docker_compose(mock_run, mock_compose, mock_env_path, mock_file):
    mock_env_path.return_value = MagicMock(exists=MagicMock(return_value=True), **{"__str__": lambda s: "/tmp/.env"})
    mock_run.return_value = MagicMock(returncode=0)
    rc = cmd_status()
    assert rc == 0
    mock_run.assert_called_once_with(
        ["docker-compose", "-f", "/tmp/docker-compose.yml", "--env-file", "/tmp/.env", "ps"]
    )


# ── Doctor ───────────────────────────────────────────────────────────────────


@patch("mateobserve.cli._dev_compose", return_value=Path("/dev/docker-compose.yml"))
@patch("mateobserve.cli._is_mateobserve_running", return_value=False)
@patch("mateobserve.cli._port_available", return_value=True)
@patch("mateobserve.cli._check_command", return_value=True)
def test_doctor_all_ok(mock_cmd, mock_port, mock_running, mock_dev):
    rc = cmd_doctor()
    assert rc == 0


@patch("mateobserve.cli._dev_compose", return_value=Path("/dev/docker-compose.yml"))
@patch("mateobserve.cli._is_mateobserve_running", return_value=False)
@patch("mateobserve.cli._port_available", return_value=True)
@patch("mateobserve.cli._check_command", return_value=False)
def test_doctor_missing_docker(mock_cmd, mock_port, mock_running, mock_dev):
    rc = cmd_doctor()
    assert rc == 1


@patch("mateobserve.cli._dev_compose", return_value=Path("/dev/docker-compose.yml"))
@patch("mateobserve.cli._is_mateobserve_running", return_value=False)
@patch("mateobserve.cli._port_available", return_value=False)
@patch("mateobserve.cli._check_command", return_value=True)
def test_doctor_ports_in_use(mock_cmd, mock_port, mock_running, mock_dev):
    rc = cmd_doctor()
    assert rc == 1


@patch("mateobserve.cli._dev_compose", return_value=Path("/dev/docker-compose.yml"))
@patch("mateobserve.cli._is_mateobserve_running", return_value=True)
@patch("mateobserve.cli._port_available", return_value=False)
@patch("mateobserve.cli._check_command", return_value=True)
def test_doctor_ports_used_by_mateobserve_is_ok(mock_cmd, mock_port, mock_running, mock_dev):
    """When MateObserve is running, occupied ports should not be errors."""
    rc = cmd_doctor()
    assert rc == 0


# ── Path helpers ─────────────────────────────────────────────────────────────


def test_data_dir_is_in_home():
    data_dir = _get_data_dir()
    assert data_dir.name == ".mateobserve"
    assert data_dir.parent == Path.home()


def test_dev_compose_points_to_docker_dir():
    result = _dev_compose()
    # In the source tree this should find docker/docker-compose.yml
    if result is not None:
        assert result.name == "docker-compose.yml"
        assert result.parent.name == "docker"
