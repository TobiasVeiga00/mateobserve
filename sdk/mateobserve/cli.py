"""MateObserve CLI — manage the observability stack."""

from __future__ import annotations

import argparse
import secrets
import shutil
import socket
import subprocess
import sys
from pathlib import Path


# ── Path helpers ─────────────────────────────────────────────────────────────


def _get_data_dir() -> Path:
    """Return the persistent MateObserve data directory (~/.mateobserve/)."""
    return Path.home() / ".mateobserve"


def _bundled_compose() -> Path:
    """Return the path to the docker-compose.yml bundled with the pip package."""
    return Path(__file__).resolve().parent / "data" / "docker-compose.yml"


def _dev_compose() -> Path | None:
    """Return compose file from source tree if running as editable install."""
    src = Path(__file__).resolve().parents[2] / "docker" / "docker-compose.yml"
    return src if src.exists() else None


def _ensure_stack_files() -> Path:
    """Ensure compose + .env exist in the data dir. Returns compose path."""
    data_dir = _get_data_dir()
    compose_dest = data_dir / "docker-compose.yml"

    # Always sync compose from the bundled package so upgrades take effect.
    data_dir.mkdir(parents=True, exist_ok=True)
    bundled = _bundled_compose()
    if not bundled.exists():
        print(
            "Error: bundled docker-compose.yml not found. "
            "Reinstall mateobserve: pip install --force-reinstall mateobserve",
            file=sys.stderr,
        )
        sys.exit(1)
    shutil.copy2(bundled, compose_dest)

    _ensure_env_file(compose_dest)
    return compose_dest


def _get_compose_file() -> Path:
    """Get the compose file — dev source tree or persistent data dir."""
    dev = _dev_compose()
    if dev is not None:
        return dev
    return _ensure_stack_files()


def _get_compose_cmd() -> list[str]:
    """Return the base compose command, preferring 'docker compose' plugin."""
    try:
        r = subprocess.run(
            ["docker", "compose", "version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        if r.returncode == 0:
            return ["docker", "compose"]
    except FileNotFoundError:
        pass
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    return ["docker", "compose"]


def _run(args: list[str]) -> int:
    try:
        return subprocess.run(args).returncode
    except FileNotFoundError:
        print(
            "Error: Docker not found. Install it from https://docs.docker.com/get-docker/",
            file=sys.stderr,
        )
        return 1


def _env_file_path(compose_file: Path) -> Path:
    """Return the .env file path next to the compose file."""
    return compose_file.parent / ".env"


def _ensure_env_file(compose_file: Path) -> Path:
    """Create a .env with random passwords if it doesn't exist yet."""
    env_path = _env_file_path(compose_file)
    if env_path.exists():
        return env_path
    compose_file.parent.mkdir(parents=True, exist_ok=True)
    password = secrets.token_urlsafe(16)
    api_key = secrets.token_urlsafe(32)
    env_path.write_text(
        f"POSTGRES_USER=mateobserve\n"
        f"POSTGRES_PASSWORD={password}\n"
        f"POSTGRES_DB=mateobserve\n"
        f"REDIS_PASSWORD={password}\n"
        f"MATEOBSERVE_API_KEY={api_key}\n"
    )
    import os as _os
    _os.chmod(env_path, 0o600)
    print(f"  Generated {env_path} with random passwords (mode 0600)")
    return env_path


# ── Commands ─────────────────────────────────────────────────────────────────


def cmd_init() -> int:
    """Set up MateObserve data directory with compose file and credentials."""
    print("🧉 Initializing MateObserve...\n")

    data_dir = _get_data_dir()
    compose_dest = data_dir / "docker-compose.yml"
    data_dir.mkdir(parents=True, exist_ok=True)

    bundled = _bundled_compose()
    if not bundled.exists():
        print(
            "  ✗ Bundled docker-compose.yml not found.\n"
            "    Reinstall: pip install --force-reinstall mateobserve",
            file=sys.stderr,
        )
        return 1

    if compose_dest.exists():
        print(f"  ✓ Compose file already exists at {compose_dest}")
    else:
        shutil.copy2(bundled, compose_dest)
        print(f"  ✓ Copied docker-compose.yml to {compose_dest}")

    env_path = _env_file_path(compose_dest)
    if env_path.exists():
        print(f"  ✓ Environment file already exists at {env_path}")
    else:
        _ensure_env_file(compose_dest)

    print(f"\n  Stack files: {data_dir}/")
    print("\n  Next steps:")
    print("    mateobserve up       # Start the stack")
    print("    mateobserve doctor   # Check environment")
    return 0


def cmd_up() -> int:
    print("🧉 Starting MateObserve stack...")
    compose_file = _get_compose_file()
    env_file = _ensure_env_file(compose_file)
    cmd = _get_compose_cmd() + ["-f", str(compose_file), "--env-file", str(env_file), "up", "-d"]
    rc = _run(cmd)
    if rc == 0:
        print("\nDashboard:  http://localhost:4000")
        print("Collector:  http://localhost:8001")
    return rc


def cmd_down() -> int:
    print("🧉 Stopping MateObserve stack...")
    compose_file = _get_compose_file()
    env_file = _env_file_path(compose_file)
    cmd = _get_compose_cmd() + ["-f", str(compose_file)]
    if env_file.exists():
        cmd += ["--env-file", str(env_file)]
    cmd.append("down")
    return _run(cmd)


def cmd_status() -> int:
    compose_file = _get_compose_file()
    env_file = _env_file_path(compose_file)
    cmd = _get_compose_cmd() + ["-f", str(compose_file)]
    if env_file.exists():
        cmd += ["--env-file", str(env_file)]
    cmd.append("ps")
    return _run(cmd)


# ── Doctor checks ────────────────────────────────────────────────────────────


def _check_command(name: str, args: list[str]) -> bool:
    try:
        subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        return False


def _port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def _is_mateobserve_running() -> bool:
    """Check if MateObserve containers are currently running."""
    dev = _dev_compose()
    if dev is not None:
        compose_file = dev
    else:
        compose_file = _get_data_dir() / "docker-compose.yml"
        if not compose_file.exists():
            return False
    try:
        env_file = _env_file_path(compose_file)
        cmd = _get_compose_cmd() + ["-f", str(compose_file)]
        if env_file.exists():
            cmd += ["--env-file", str(env_file)]
        cmd += ["ps", "-q"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return bool(result.stdout.strip())
    except Exception:
        return False


def cmd_doctor() -> int:
    print("🧉 Checking MateObserve environment...\n")
    ok = True

    # Docker
    if _check_command("docker", ["docker", "info"]):
        print("  ✓ Docker installed")
    else:
        print("  ✗ Docker not found — install it from https://docs.docker.com/get-docker/")
        ok = False

    # Docker Compose
    compose_cmd = _get_compose_cmd()
    if _check_command("docker compose", compose_cmd + ["version"]):
        print("  ✓ Docker Compose available")
    else:
        print("  ✗ Docker Compose not available — install Docker Compose")
        ok = False

    # Check if stack is already running
    stack_running = _is_mateobserve_running()

    # Port 4000 (dashboard)
    if _port_available(4000):
        print("  ✓ Port 4000 available (dashboard)")
    elif stack_running:
        print("  ✓ Port 4000 in use by MateObserve (stack is running)")
    else:
        print("  ✗ Port 4000 in use by another process — the dashboard needs this port")
        ok = False

    # Port 8001 (collector)
    if _port_available(8001):
        print("  ✓ Port 8001 available (collector)")
    elif stack_running:
        print("  ✓ Port 8001 in use by MateObserve (stack is running)")
    else:
        print("  ✗ Port 8001 in use by another process — the collector needs this port")
        ok = False

    # Stack files
    data_dir = _get_data_dir()
    compose_exists = (data_dir / "docker-compose.yml").exists() or _dev_compose() is not None
    if compose_exists:
        print("  ✓ Stack files configured")
    else:
        print("  ✗ Stack not initialized — run: mateobserve init")
        ok = False

    print()
    if ok:
        if stack_running:
            print("MateObserve is running. Dashboard: http://localhost:4000")
        else:
            print("Environment looks good. Run: mateobserve up")
        return 0
    else:
        print("Some checks failed. Fix the issues above and try again.")
        return 1


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="mateobserve",
        description="MateObserve — simple observability for Python APIs 🧉",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("init", help="Initialize MateObserve in this environment")
    sub.add_parser("up", help="Start the MateObserve stack")
    sub.add_parser("down", help="Stop the MateObserve stack")
    sub.add_parser("status", help="Show running containers")
    sub.add_parser("doctor", help="Check environment readiness")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "up": cmd_up,
        "down": cmd_down,
        "status": cmd_status,
        "doctor": cmd_doctor,
    }

    if args.command is None:
        parser.print_help()
        sys.exit(1)

    sys.exit(commands[args.command]())


if __name__ == "__main__":
    main()
