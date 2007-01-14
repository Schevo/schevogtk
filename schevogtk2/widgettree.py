"""WidgetTree class.

For copyright, license, and warranty, see bottom of file.
"""

import sys
from schevo.lib import optimize

import os

from schevogtk2 import gazpacholoader

from gazpacho.loader.loader import ObjectBuilder
## from kiwi.ui import dialogs
from kiwi.environ import environ
from kiwi.ui.views import GladeSignalBroker
## from kiwi.ui.gazpacholoader import GazpachoWidgetTree as WidgetTree


class Builder(ObjectBuilder):

    def find_resource(self, filename):
        return environ.find_resource("pixmaps",  filename)


class WidgetTree:
    """Example class of GladeAdaptor that uses Gazpacho loader to load the
    glade files
    """
    def __init__(self, view, gladefile, widgets, gladename=None, domain=None):

        if not gladefile:
            raise ValueError("A gladefile wasn't provided.")
        elif not isinstance(gladefile, basestring):
            raise TypeError(
                  "gladefile should be a string, found %s" % type(gladefile))
        filename = os.path.splitext(os.path.basename(gladefile))[0]
        self._filename = filename + '.glade'
        self._view = view
        self._gladefile = environ.find_resource("glade", self._filename)
        self._widgets = (widgets or view.widgets or [])[:]
        self.gladename = gladename or filename
##         self._showwarning = warnings.showwarning
##         warnings.showwarning = self._on_load_warning
        self._tree = Builder(self._gladefile, domain=domain)
##         warnings.showwarning = self._showwarning
        if not self._widgets:
            self._widgets = [w.get_data("gazpacho::object-id")
                             for w in self._tree.get_widgets()]
        self._attach_widgets()

##     def _on_load_warning(self, warning, category, file, line):
##         self._showwarning('while loading glade file: %s' % warning,
##                           category, self._filename, '???')

    def _attach_widgets(self):
        # Attach widgets in the widgetlist to the view specified, so
        # widgets = [label1, button1] -> view.label1, view.button1
        for w in self._widgets:
            widget = self._tree.get_widget(w)
            if widget is not None:
                setattr(self._view, w, widget)
            else:
                log.warn("Widget %s was not found in glade widget tree." % w)

    def get_widget(self, name):
        """Retrieves the named widget from the View (or glade tree)"""
        name = name.replace('.', '_')
        name = name.replace('-', '_')
        widget = self._tree.get_widget(name)
        if widget is None:
            raise AttributeError(
                  "Widget %s not found in view %s" % (name, self._view))
        return widget

    def get_widgets(self):
        return self._tree.get_widgets()

    def signal_autoconnect(self, dic):
        self._tree.signal_autoconnect(dic)

    def get_sizegroups(self):
        return self._tree.sizegroups


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
