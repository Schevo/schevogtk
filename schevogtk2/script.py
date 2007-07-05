"""PyGTK Database Navigator command.

For copyright, license, and warranty, see bottom of file.
"""

import os
import thread

## import louie

from schevogtk2.application import Application

from schevo.script.command import Command
from schevo.script import opt


USAGE = """\
schevo gnav [options] [DBFILE]

DBFILE: The database file to use.  If not specified you may open a
database using the File menu."""


def _parser():
    p = opt.parser(USAGE)
    p.add_option('-c', '--pycrust', dest='pycrust',
                 help='Open a PyCrust session in a separate thread.',
                 action='store_true', default=False,
                 )
    return p


def start_pycrust(**locals):
    """Start PyCrust in a separate thread."""
    import wx
    class App(wx.App):
        def OnInit(self):
            from wx import py
            wx.InitAllImageHandlers()
            self.frame = py.crust.CrustFrame(locals=locals)
            self.frame.SetSize((800, 600))
            self.frame.Show()
            self.SetTopWindow(self.frame)
            return True
    app = App(0)
    thread.start_new_thread(app.MainLoop, ())


class Navigator(Command):

    name = 'Database Navigator'
    description = 'Navigate Schevo databases using a GTK2 GUI.'

    def main(self, arg0, args):
        print
        print
        parser = _parser()
        options, args = parser.parse_args(list(args))
        if args:
            db_filename = args.pop(0)
            if not os.path.isfile(db_filename):
                print 'File %r must already exist' % db_filename
                return 1
        else:
            db_filename = None
        # Create PyGTK application.
        app = Application()
##         # Install Louie plugin.
##         louie.install_plugin(louie.QtWidgetPlugin())
        # Open the database.
        if db_filename:
            print 'Opened database', db_filename
            app.database_open(db_filename)
        # Start PyCrust if requested.
        if options.pycrust:
            start_pycrust(app=app)
            print 'PyCrust started.'
        # Start PyGtk event loop.
        print 'Starting Navigator UI...'
        app.run()


start = Navigator


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
