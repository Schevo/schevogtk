"""Initialization of PyGTK.

For copyright, license, and warranty, see bottom of file.
"""

import sys

available = False

try:
    import pygtk
except ImportError:
    pass
else:
    if not sys.platform == 'win32':
        # Hack to keep py2exe happy on the Windows platform.
        pygtk.require('2.0')
    try:
        import kiwi
    except ImportError:
        pass
    else:
        try:
            import gtk
        except RuntimeError:
            # Raised if PyGTK is installed on a Linux system,
            # but an X display is not available.
            pass
        else:
            available = True


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
