"""Main application window."""

import os
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, GObject

from ..cleaner.base import Cleaner, CleanItem, CleanResult
from ..cleaner.cache import PacmanCacheCleaner, UserCacheCleaner
from ..cleaner.logs import SystemLogsCleaner, JournalCleaner
from ..cleaner.packages import OrphanPackagesCleaner
from ..cleaner.browser import BrowserCacheCleaner

CLEANERS = [
    PacmanCacheCleaner(),
    UserCacheCleaner(),
    SystemLogsCleaner(),
    JournalCleaner(),
    OrphanPackagesCleaner(),
    BrowserCacheCleaner(),
]


def human_size(n):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PiB"


class CleanerRow(Gtk.ListBoxRow):
    def __init__(self, item: CleanItem, cleaner_index: int):
        super().__init__()
        self.item = item
        self.cleaner_index = cleaner_index
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(12)
        box.set_margin_end(12)

        check = Gtk.CheckButton()
        check.set_active(item.selected)
        check.connect("toggled", self._on_toggle)
        self.check = check
        box.append(check)

        label_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        label_box.set_hexpand(True)
        name_label = Gtk.Label(label=item.description or item.path)
        name_label.set_halign(Gtk.Align.START)
        name_label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        path_label = Gtk.Label(label=item.path)
        path_label.set_halign(Gtk.Align.START)
        path_label.add_css_class("dim-label")
        path_label.set_ellipsize(3)
        label_box.append(name_label)
        label_box.append(path_label)
        box.append(label_box)

        size_label = Gtk.Label(label=human_size(item.size))
        size_label.set_halign(Gtk.Align.END)
        box.append(size_label)

        self.set_child(box)

    def _on_toggle(self, btn):
        self.item.selected = btn.get_active()


class CategoryPage(Gtk.Box):
    """Page showing items for a single cleaner category."""

    def __init__(self, cleaner: Cleaner, index: int, window):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.cleaner = cleaner
        self.index = index
        self.window = window
        self.items = []
        self.rows = []

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header.set_margin_top(12)
        header.set_margin_bottom(12)
        header.set_margin_start(12)
        header.set_margin_end(12)

        title = Gtk.Label(label=cleaner.name)
        title.add_css_class("title-2")
        title.set_halign(Gtk.Align.START)
        title.set_hexpand(True)
        header.append(title)

        self.status_label = Gtk.Label(label="Not scanned")
        self.status_label.add_css_class("dim-label")
        header.append(self.status_label)

        scan_btn = Gtk.Button(label="Scan")
        scan_btn.connect("clicked", self._on_scan)
        header.append(scan_btn)

        clean_btn = Gtk.Button(label="Clean")
        clean_btn.add_css_class("destructive-action")
        clean_btn.connect("clicked", self._on_clean)
        header.append(clean_btn)

        self.append(header)

        # Progress bar
        self.progress = Gtk.ProgressBar()
        self.progress.set_margin_start(12)
        self.progress.set_margin_end(12)
        self.progress.set_visible(False)
        self.append(self.progress)

        # Scrolled list
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        scrolled.set_child(self.listbox)
        self.append(scrolled)

        # Summary footer
        self.summary = Gtk.Label(label="")
        self.summary.set_margin_top(6)
        self.summary.set_margin_bottom(6)
        self.summary.set_margin_start(12)
        self.summary.set_margin_end(12)
        self.summary.set_halign(Gtk.Align.START)
        self.append(self.summary)

    def _on_scan(self, _btn):
        self.progress.set_visible(True)
        self.progress.set_fraction(0.0)
        # clear children
        while True:
            child = self.listbox.get_first_child()
            if child is None:
                break
            self.listbox.remove(child)
        self.rows = []

        def progress(frac, text):
            GLib.idle_add(self.progress.set_fraction, frac)

        items = self.cleaner.scan(progress)
        # Sort by size descending (largest first)
        items.sort(key=lambda x: x.size, reverse=True)
        self.items = items
        for idx, it in enumerate(items):
            row = CleanerRow(it, self.index)
            self.listbox.append(row)
            self.rows.append(row)
        self.progress.set_visible(False)
        total = sum(i.size for i in items if i.selected)
        self.status_label.set_label(f"{len(items)} items")
        self.summary.set_label(f"Selected: {human_size(total)}")
        self.window.update_total()

    def _on_clean(self, _btn):
        selected = [it for it in self.items if it.selected]
        if not selected:
            return
        # Confirmation dialog
        dlg = Adw.MessageDialog.new(self.window, "Clean selected items?",
                                    f"This will remove {len(selected)} items "
                                    f"({human_size(sum(i.size for i in selected))}).")
        dlg.add_response("cancel", "Cancel")
        dlg.add_response("clean", "Clean")
        dlg.set_response_appearance("clean", Adw.ResponseAppearance.DESTRUCTIVE)
        dlg.connect("response", self._do_clean, selected)
        dlg.present()
        return

    def _do_clean(self, dlg, response, selected):
        if response != "clean":
            return
        self.progress.set_visible(True)
        self.progress.set_fraction(0.0)

        def progress(frac, text):
            GLib.idle_add(self.progress.set_fraction, frac)

        result = self.cleaner.clean(selected, progress)
        self.progress.set_visible(False)

        # Remove successfully cleaned items from list
        for it in selected:
            if (it.path not in ("journalctl --vacuum-time",) and
                    not os.path.exists(it.path)) or it.path == "journalctl --vacuum-time":
                if it in self.items:
                    self.items.remove(it)
        # rebuild
        while True:
            child = self.listbox.get_first_child()
            if child is None:
                break
            self.listbox.remove(child)
        self.rows = []
        for it in self.items:
            row = CleanerRow(it, self.index)
            self.listbox.append(row)
            self.rows.append(row)

        freed = human_size(result.freed_bytes)
        msg = f"Freed {freed}, removed {result.removed_count} items."
        if result.errors:
            msg += f" ({len(result.errors)} errors)"
        self.summary.set_label(msg)
        self.status_label.set_label(f"{len(self.items)} items")
        self.window.update_total()
        self.window.show_toast(msg)


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("ArchClean")
        self.set_default_size(900, 620)

        # Toast overlay
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)

        # Main layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toast_overlay.set_child(main_box)

        # Header bar
        header = Adw.HeaderBar()
        main_box.append(header)

        title_widget = Adw.WindowTitle(title="ArchClean", subtitle="Modern system cleaner for Arch Linux")
        header.set_title_widget(title_widget)

        scan_all_btn = Gtk.Button(label="Scan All")
        scan_all_btn.connect("clicked", self._on_scan_all)
        header.pack_start(scan_all_btn)

        clean_all_btn = Gtk.Button(label="Clean All")
        clean_all_btn.add_css_class("destructive-action")
        clean_all_btn.connect("clicked", self._on_clean_all)
        header.pack_end(clean_all_btn)

        about_btn = Gtk.Button(icon_name="help-about-symbolic")
        about_btn.connect("clicked", self._on_about)
        header.pack_end(about_btn)

        self.stack = Adw.ViewStack()

        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)
        main_box.append(content_box)

        self.pages = []
        for idx, cleaner in enumerate(CLEANERS):
            page = CategoryPage(cleaner, idx, self)
            self.stack.add_titled(page, cleaner.name.lower().replace(" ", "-"), cleaner.name)
            self.pages.append(page)

        content_box.append(self.stack)

        # Bottom bar with total
        bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        bottom.set_margin_top(6)
        bottom.set_margin_bottom(6)
        bottom.set_margin_start(12)
        bottom.set_margin_end(12)
        self.total_label = Gtk.Label(label="Total selected: 0 B")
        self.total_label.set_hexpand(True)
        self.total_label.set_halign(Gtk.Align.START)
        bottom.append(self.total_label)
        main_box.append(bottom)

        # View switcher bar at bottom
        vs_bar = Adw.ViewSwitcherBar()
        vs_bar.set_stack(self.stack)
        vs_bar.set_reveal(True)
        main_box.append(vs_bar)

    def _on_about(self, _btn):
        dlg = Adw.AboutDialog.new()
        dlg.set_application_name("ArchClean")
        dlg.set_application_icon("archclean")
        dlg.set_developer_name("ArchClean Contributors")
        dlg.set_version(__import__("archclean").__version__)
        dlg.set_comments("A modern system cleaner for Arch Linux")
        dlg.set_license("MIT License\n\nPermission is hereby granted, free of charge...")
        dlg.present(self)

    def update_total(self):
        total = 0
        for page in self.pages:
            for it in page.items:
                if it.selected:
                    total += it.size
        self.total_label.set_label(f"Total selected: {human_size(total)}")

    def _on_scan_all(self, _btn):
        for page in self.pages:
            page._on_scan(None)

    def _on_clean_all(self, _btn):
        total_items = sum(len([it for it in p.items if it.selected]) for p in self.pages)
        if total_items == 0:
            return
        dlg = Adw.MessageDialog.new(self, "Clean all selected items?",
                                    f"This will remove {total_items} items across all categories.")
        dlg.add_response("cancel", "Cancel")
        dlg.add_response("clean", "Clean All")
        dlg.set_response_appearance("clean", Adw.ResponseAppearance.DESTRUCTIVE)
        dlg.connect("response", self._do_clean_all)
        dlg.present()

    def _do_clean_all(self, dlg, response):
        if response != "clean":
            return
        for page in self.pages:
            page._do_clean(None, "clean", [it for it in page.items if it.selected])

    def show_toast(self, msg):
        toast = Adw.Toast(title=msg)
        self.toast_overlay.add_toast(toast)
