"""Cursor-changing context manager."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

import gtk
from gtk import gdk


WATCH = gdk.Cursor(gdk.WATCH)


class TemporaryCursor(object):

    def __init__(self, window, cursor=WATCH, exit_cursor=None):
        self.window = window
        self.cursor = cursor
        self.exit_cursor = exit_cursor

    def __enter__(self):
        window = self.window.toplevel.window
        if window is not None:
            window.set_cursor(self.cursor)
            while gtk.events_pending():
                gtk.main_iteration()

    def __exit__(self, exc_type, exc_val, exc_tb):
        window = self.window.toplevel.window
        if window is not None:
            window.set_cursor(self.exit_cursor)
            while gtk.events_pending():
                gtk.main_iteration()
        # Do not ignore exception.
        return False


optimize.bind_all(sys.modules[__name__])  # Last line of module.
