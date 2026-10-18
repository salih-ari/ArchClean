"""Pacman and user cache cleaners."""

import os
import shutil
from .base import Cleaner, CleanItem, CleanResult
from ..utils.pacman import get_cache_size, is_pacman_available


class PacmanCacheCleaner(Cleaner):
    name = "Pacman Cache"
    description = "Old package archives in /var/cache/pacman/pkg"

    def scan(self, progress_cb=None):
        items = []
        path = "/var/cache/pacman/pkg"
        if not os.path.isdir(path):
            return items
        try:
            entries = sorted(os.listdir(path))
        except OSError:
            return items
        total = len(entries)
        for i, name in enumerate(entries):
            full = os.path.join(path, name)
            if not os.path.isfile(full):
                continue
            try:
                size = os.path.getsize(full)
            except OSError:
                size = 0
            items.append(CleanItem(path=full, size=size, description=name))
            if progress_cb:
                progress_cb((i + 1) / max(total, 1), name)
        return items

    def clean(self, items, progress_cb=None):
        result = CleanResult()
        selected = [it for it in items if it.selected]
        total = len(selected)
        from ..utils.elevate import remove_paths
        paths = [it.path for it in selected]
        removed, errors = remove_paths(paths)
        # Map removed count back: assume freed bytes for successfully removed
        removed_set = set(p for p in paths if not os.path.exists(p))
        for it in selected:
            if it.path in removed_set or not os.path.exists(it.path):
                result.freed_bytes += it.size
        result.removed_count = removed
        for e in errors:
            result.errors.append(e)
            result.success = False
        if progress_cb:
            progress_cb(1.0, "done")
        return result


class UserCacheCleaner(Cleaner):
    name = "User Cache"
    description = "Application caches in ~/.cache"

    def __init__(self, cache_dir=None):
        self.cache_dir = cache_dir or os.path.expanduser("~/.cache")

    def scan(self, progress_cb=None):
        items = []
        if not os.path.isdir(self.cache_dir):
            return items
        try:
            entries = sorted(os.listdir(self.cache_dir))
        except OSError:
            return items
        total = len(entries)
        for i, name in enumerate(entries):
            full = os.path.join(self.cache_dir, name)
            size = self._dir_size(full) if os.path.isdir(full) else (os.path.getsize(full) if os.path.isfile(full) else 0)
            items.append(CleanItem(path=full, size=size, description=name))
            if progress_cb:
                progress_cb((i + 1) / max(total, 1), name)
        return items

    def clean(self, items, progress_cb=None):
        result = CleanResult()
        total = len(items)
        for i, item in enumerate(items):
            if not item.selected:
                continue
            try:
                if os.path.isdir(item.path) and not os.path.islink(item.path):
                    shutil.rmtree(item.path)
                else:
                    os.remove(item.path)
                result.freed_bytes += item.size
                result.removed_count += 1
            except OSError as e:
                result.errors.append(f"{item.path}: {e}")
                result.success = False
            if progress_cb:
                progress_cb((i + 1) / max(total, 1), item.path)
        return result

    @staticmethod
    def _dir_size(path):
        total = 0
        for root, _dirs, files in os.walk(path):
            for f in files:
                try:
                    total += os.path.getsize(os.path.join(root, f))
                except OSError:
                    pass
        return total
