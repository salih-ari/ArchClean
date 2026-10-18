"""Log file cleaners."""

import os
import glob
from .base import Cleaner, CleanItem, CleanResult


class SystemLogsCleaner(Cleaner):
    name = "System Logs"
    description = "Old log files in /var/log"

    def __init__(self, log_dir="/var/log"):
        self.log_dir = log_dir

    def scan(self, progress_cb=None):
        items = []
        if not os.path.isdir(self.log_dir):
            return items
        patterns = ["*.log", "*.log.*", "*.old", "*.gz"]
        seen = set()
        for pat in patterns:
            for full in glob.glob(os.path.join(self.log_dir, pat)):
                if full in seen or not os.path.isfile(full):
                    continue
                seen.add(full)
                try:
                    size = os.path.getsize(full)
                except OSError:
                    size = 0
                items.append(CleanItem(path=full, size=size, description=os.path.basename(full)))
        # Also rotated logs in subdirs (limited depth)
        for root, dirs, files in os.walk(self.log_dir):
            # avoid deep recursion into huge trees
            if root.count(os.sep) - self.log_dir.count(os.sep) > 2:
                dirs[:] = []
                continue
            for f in files:
                if f.endswith((".log.1", ".log.2", ".gz", ".old", ".1")):
                    full = os.path.join(root, f)
                    if full in seen:
                        continue
                    seen.add(full)
                    try:
                        size = os.path.getsize(full)
                    except OSError:
                        size = 0
                    items.append(CleanItem(path=full, size=size, description=os.path.relpath(full, self.log_dir)))
        if progress_cb:
            progress_cb(1.0, f"{len(items)} items")
        return items

    def clean(self, items, progress_cb=None):
        result = CleanResult()
        selected = [it for it in items if it.selected]
        from ..utils.elevate import remove_paths
        paths = [it.path for it in selected]
        removed, errors = remove_paths(paths)
        removed_set = set(p for p in paths if not os.path.exists(p))
        for it in selected:
            if it.path in removed_set:
                result.freed_bytes += it.size
        result.removed_count = removed
        for e in errors:
            result.errors.append(e)
            result.success = False
        if progress_cb:
            progress_cb(1.0, "done")
        return result


class JournalCleaner(Cleaner):
    name = "Systemd Journal"
    description = "Vacuum systemd journal (keeps recent entries)"

    def __init__(self, keep_days=7):
        self.keep_days = keep_days

    def scan(self, progress_cb=None):
        # Represent as a single virtual item
        size = self._journal_size()
        item = CleanItem(
            path="journalctl --vacuum-time",
            size=size,
            description=f"Vacuum journal older than {self.keep_days} days",
        )
        if progress_cb:
            progress_cb(1.0, "journal")
        return [item]

    def clean(self, items, progress_cb=None):
        result = CleanResult()
        import subprocess
        for item in items:
            if not item.selected:
                continue
            try:
                subprocess.run(
                    ["journalctl", f"--vacuum-time={self.keep_days}d"],
                    check=True, capture_output=True, text=True,
                )
                result.freed_bytes += item.size
                result.removed_count += 1
            except Exception as e:
                result.errors.append(str(e))
                result.success = False
        if progress_cb:
            progress_cb(1.0, "done")
        return result

    @staticmethod
    def _journal_size():
        import subprocess
        try:
            r = subprocess.run(["journalctl", "--disk-usage"], capture_output=True, text=True)
            # parse "Archived and active journals take up X in file system."
            import re
            m = re.search(r"take up\s+([\d.]+)\s*([KMGT]?)", r.stdout)
            if m:
                val = float(m.group(1))
                unit = m.group(2)
                mult = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}.get(unit, 1)
                return int(val * mult)
        except Exception:
            pass
        return 0
