"""Elevation helpers for system-level file operations."""

import os
import subprocess
import tempfile


def is_root() -> bool:
    return os.geteuid() == 0


def remove_paths(paths, *, use_pkexec=True) -> tuple[int, list[str]]:
    """Remove a list of file paths, elevating via pkexec if needed.

    Returns (removed_count, errors).
    """
    if not paths:
        return 0, []
    if is_root():
        return _remove_direct(paths)
    if not use_pkexec:
        return _remove_direct(paths)
    # Write a helper script and run it via pkexec
    fd, script = tempfile.mkstemp(prefix="archclean_", suffix=".sh")
    try:
        with os.fdopen(fd, "w") as f:
            f.write("#!/bin/bash\nset -u\n")
            for p in paths:
                f.write(f"rm -f -- {shell_quote(p)}\n")
        os.chmod(script, 0o700)
        proc = subprocess.run(
            ["pkexec", "/bin/bash", script],
            capture_output=True, text=True,
            timeout=300,
        )
        # Count successes by checking existence
        removed = sum(1 for p in paths if not os.path.exists(p))
        errors = [p for p in paths if os.path.exists(p)]
        errors = [f"{p}: permission denied or failed" for p in errors]
        if removed == 0 and proc.returncode != 0:
            # pkexec failed (e.g. cancelled); fall back to direct
            return _remove_direct(paths)
        return removed, errors
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return _remove_direct(paths)
    finally:
        try:
            os.remove(script)
        except OSError:
            pass


def shell_quote(s):
    import shlex
    return shlex.quote(s)


def _remove_direct(paths):
    removed = 0
    errors = []
    for p in paths:
        try:
            if os.path.isdir(p) and not os.path.islink(p):
                import shutil
                shutil.rmtree(p)
            else:
                os.remove(p)
            removed += 1
        except OSError as e:
            errors.append(f"{p}: {e}")
    return removed, errors
