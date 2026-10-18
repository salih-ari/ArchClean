"""Package-related cleaners (orphans, unused deps)."""

import subprocess
from .base import Cleaner, CleanItem, CleanResult
from ..utils.pacman import list_orphan_packages, is_pacman_available


class OrphanPackagesCleaner(Cleaner):
    name = "Orphan Packages"
    description = "Packages no longer required by any installed package"

    def scan(self, progress_cb=None):
        items = []
        if not is_pacman_available():
            return items
        orphans = list_orphan_packages()
        total = len(orphans)
        for i, name in enumerate(orphans):
            # estimate size via pacman -Qi
            size = self._package_size(name)
            items.append(CleanItem(path=name, size=size, description=name))
            if progress_cb:
                progress_cb((i + 1) / max(total, 1), name)
        return items

    def clean(self, items, progress_cb=None):
        result = CleanResult()
        selected = [it for it in items if it.selected]
        if not selected:
            return result
        names = [it.path for it in selected]
        try:
            subprocess.run(
                ["sudo", "pacman", "-Rns", "--noconfirm"] + names,
                check=True, capture_output=True, text=True,
            )
            for it in selected:
                result.freed_bytes += it.size
                result.removed_count += 1
        except Exception as e:
            result.errors.append(str(e))
            result.success = False
        if progress_cb:
            progress_cb(1.0, "done")
        return result

    @staticmethod
    def _package_size(name):
        try:
            r = subprocess.run(
                ["pacman", "-Qi", name], capture_output=True, text=True, check=False)
            for line in r.stdout.splitlines():
                if line.lower().startswith("installed size"):
                    # "Installed Size  : 12.00 MiB"
                    parts = line.split(":", 1)[-1].strip().split()
                    if len(parts) >= 2:
                        val = float(parts[0])
                        unit = parts[1].lower()
                        mult = {"b": 1, "kib": 1024, "mib": 1024**2,
                                "gib": 1024**3, "kb": 1000, "mb": 1000**2,
                                "gb": 1000**3}.get(unit, 1)
                        return int(val * mult)
        except Exception:
            pass
        return 0
