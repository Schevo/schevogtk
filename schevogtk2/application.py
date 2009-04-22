"""Application class."""

# Copyright (c) 2001-2009 ElevenCraft Inc.
# See LICENSE for details.

import sys
from schevo.lib import optimize

from schevogtk2.navigator import NavigatorWindow


class Application(object):

    WindowClass = NavigatorWindow

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
