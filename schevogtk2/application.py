"""Application class.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

from schevogtk2 import gazpacholoader
from schevogtk2 import navigator


class Application(object):

    WindowClass = navigator.Window

    def __init__(self, window_class=None):
        if window_class is None:
            window_class = self.WindowClass
        self.window = window_class()

    def database_open(self, filename):
        return self.window.database_open(filename)

    @property
    def db(self):
        return self.window._db

    def run(self):
        self.window.show_and_loop()

##     def show(self):
##         self.window.show()

##     def shutdown(self, *args):
##         gtk.main_quit()


if __name__ == '__main__':
    app = Application()
    app.run()


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
