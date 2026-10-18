"""Browser cache cleaners."""

import os
import glob
import shutil
from .base import Cleaner, CleanItem, CleanResult


BROWSER_CACHE_PATHS = {
    "Firefox": "~/.cache/mozilla/firefox",
    "Chrome": "~/.cache/google-chrome",
    "Chromium": "~/.cache/chromium",
    "Brave": "~/.cache/BraveSoftware",
}


class BrowserCacheCleaner(Cleaner):
    name = "Browser Caches"
    description = "Cached web data from common browsers"

    def scan(self, progress_cb=None):
        items = []
        for browser, path in BROWSER_CACHE_PATHS.items():
            full = os.path.expanduser(path)
            if not os.path.isdir(full):
                continue
            size = self._dir_size(full)
            items.append(CleanItem(path=full, size=size, description=browser))
        if progress_cb:
            progress_cb(1.0, f"{len(items)} browsers")
        return items

    def clean(self, items, progress_cb=None):
        result = CleanResult()
        total = len(items)
        for i, item in enumerate(items):
            if not item.selected:
                continue
            try:
                # Remove contents but keep directory
                if os.path.isdir(item.path):
                    for entry in os.listdir(item.path):
                        p = os.path.join(item.path, entry)
                        if os.path.isdir(p) and not os.path.islink(p):
                            shutil.rmtree(p, ignore_errors=True)
                        else:
                            try:
                                os.remove(p)
                            except OSError:
                                pass
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
