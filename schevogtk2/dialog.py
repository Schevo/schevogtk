"""Dialog helpers.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import gtk


def open(title, parent=None, patterns=[], filter=None, folder=None):
    """Display an open dialog and return a filename."""
    filechooser = gtk.FileChooserDialog(title, parent,
                                        gtk.FILE_CHOOSER_ACTION_OPEN,
                                        (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                                         gtk.STOCK_OPEN, gtk.RESPONSE_OK))
    if patterns or filter:
        if not filter:
            filter = gtk.FileFilter()
            for pattern in patterns:
                filter.add_pattern(pattern)
        filechooser.set_filter(filter)
    filechooser.set_default_response(gtk.RESPONSE_OK)
    if folder:
        filechooser.set_current_folder(folder)
    response = filechooser.run()
    if response != gtk.RESPONSE_OK:
        filechooser.destroy()
        return
    path = filechooser.get_filename()
    filechooser.destroy()
    return path


optimize.bind_all(sys.modules[__name__])  # Last line of module.


# Copyright (C) 2001-2006 Orbtech, L.L.C.
#
# Schevo
# http://schevo.org/
#
# Orbtech
# 709 East Jackson Road
# Saint Louis, MO  63119-4241
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
