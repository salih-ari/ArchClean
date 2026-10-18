"""Application entry point."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from . import __app_id__, __version__
from .ui.main_window import MainWindow


class ArchCleanApplication(Adw.Application):
    def __init__(self):
        super().__init__(application_id=__app_id__, flags=0)

    def do_activate(self):
        win = self.props.active_window
        if win is None:
            win = MainWindow(self)
        win.present()


def main():
    app = ArchCleanApplication()
    return app.run(None)


if __name__ == "__main__":
    main()
