"""Cursor-changing context manager.

For copyright, license, and warranty, see bottom of file.
"""

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


# Copyright (C) 2001-2007 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# Saint Louis, MO
# http://orbtech.com/
#
# This toolkit is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This toolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
