"""Helpers around the pacman package manager."""

import subprocess
import shutil


def is_pacman_available() -> bool:
    return shutil.which("pacman") is not None


def run_pacman(args, *, check=True, capture=True) -> subprocess.CompletedProcess:
    """Run a pacman command, optionally capturing output."""
    cmd = ["pacman"] + list(args)
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
    )


def get_cache_size() -> int:
    """Return total size (bytes) of /var/cache/pacman/pkg."""
    import os
    path = "/var/cache/pacman/pkg"
    total = 0
    if not os.path.isdir(path):
        return 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def list_orphan_packages() -> list[str]:
    """Return list of orphaned package names (pacman -Qtdq)."""
    if not is_pacman_available():
        return []
    try:
        result = run_pacman(["-Qtdq"], check=False)
    except Exception:
        return []
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def list_unused_repos_cache() -> list[str]:
    """List cached package files that are no longer installed."""
    if not is_pacman_available():
        return []
    try:
        result = run_pacman(["-Sc", "--print"], check=False)
    except Exception:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]
